package main

import (
	"bufio"
	"bytes"
	"database/sql"
	"encoding/json"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"sort"
	"strings"
	"sync"
	"time"

	_ "github.com/mattn/go-sqlite3"
	"github.com/fatih/color"
)

// --- Data structures ---

type Test struct {
	ID     string   `json:"id"`
	Task   string   `json:"task"`
	Ground []string `json:"ground"`
	Blind  bool     `json:"blind"`
}

type TestDir struct {
	Test   Test
	Dir    string // tests/dotdog/ or tests/raw/
	Sample string // tests/dotdog/sample/ or tests/raw/sample/
	Grader string // tests/dotdog/grader.py or tests/grader.py
}

type Agent struct {
	ID      string
	Name    string
	CmdTpl  string // e.g. "hermes chat -q {task}"
}

type RunResult struct {
	Agent   string
	TestID  string
	AgentID string
	Input   int
	Output  int
	Passed  bool
	Err     error
}

type Results struct {
	Timestamp string                 `json:"timestamp"`
	Model     string                 `json:"model"`
	Runs      map[string]RunResult   `json:"runs"` // key: agentID:testID
}

// --- Config ---

var agents = []Agent{
	{"hermes", "hermes", "hermes chat -q {task}"},
	{"hermes_dag", "hermes + dotdog", "hermes chat -q {task}"},
	{"collar", "collar", "collar chat -q {task}"},
	{"collar_dag", "collar + dotdog", "collar chat -q {task}"},
}

var agentColors = map[string]string{
	"hermes":     "cyan",
	"hermes_dag": "magenta",
	"collar":     "yellow",
	"collar_dag": "green",
}

// --- Main ---

func main() {
	scriptDir, _ := filepath.Abs(filepath.Dir(os.Args[0]))
	if len(os.Args) > 1 && os.Args[1] == "--terminal" {
		runTerminalBench(scriptDir)
		return
	}

	model := "deepseek-v4-pro"
	if len(os.Args) > 1 && !strings.HasPrefix(os.Args[1], "--") {
		model = os.Args[1]
	}

	testDirs := loadTests(scriptDir)
	if len(testDirs) == 0 {
		fmt.Println("No tests found in tests/")
		os.Exit(1)
	}

	fmt.Printf("\n  dogbench v4  %d agents × %d tests = %d total\n\n", len(agents), len(testDirs), len(agents)*len(testDirs))

	// Run all agent×test combinations in parallel
	var wg sync.WaitGroup
	results := make(chan RunResult, len(agents)*len(testDirs))

	for _, agent := range agents {
		for _, td := range testDirs {
			wg.Add(1)
			go func(a Agent, t TestDir) {
				defer wg.Done()
				result := runAgent(a, t, scriptDir)
				results <- result
			}(agent, td)
		}
	}

	// Close results channel when all done
	go func() {
		wg.Wait()
		close(results)
	}()

	// Collect results
	allResults := make(map[string]RunResult)
	for r := range results {
		key := r.AgentID + ":" + r.TestID
		allResults[key] = r
		status := color.RedString("✗")
		if r.Passed {
			status = color.GreenString("✓")
		}
		c := colorForAgent(r.AgentID)
		fmt.Printf("  %-20s %-10s %s %st/%st\n", c.Sprintf("%-20s", r.Agent), r.TestID, status, fmtInt(r.Input), fmtInt(r.Output))
	}

	// Summary table
	fmt.Printf("\n  %-22s %-10s %4s %10s %9s %10s %8s\n", "Agent", "Test", "Pass", "Avg In", "Avg Out", "Total", "Cost")
	fmt.Println("  " + strings.Repeat("-", 80))

	for _, agent := range agents {
		for _, td := range testDirs {
			key := agent.ID + ":" + td.Test.ID
			r := allResults[key]
			c := colorForAgent(agent.ID)
			passStr := color.RedString("✗")
			if r.Passed {
				passStr = color.GreenString("✓")
			}
			total := r.Input + r.Output
			cost := calcCost(r.Input, r.Output, model)
			fmt.Printf("  %-22s %-10s %s %10s %9s %10s $%7.4f\n",
				c.Sprintf("%-22s", agent.Name), td.Test.ID, passStr,
				fmtInt(r.Input), fmtInt(r.Output), fmtInt(total), cost)
		}
	}

	// Write results.json
	writeResults(scriptDir, allResults, model)
	fmt.Println()
}

// --- Test loading ---

func loadTests(scriptDir string) []TestDir {
	testsDir := filepath.Join(scriptDir, "tests")
	entries, err := os.ReadDir(testsDir)
	if err != nil {
		return nil
	}

	var result []TestDir
	for _, entry := range entries {
		if !entry.IsDir() {
			continue
		}
		testFile := filepath.Join(testsDir, entry.Name(), "test.json")
		data, err := os.ReadFile(testFile)
		if err != nil {
			continue
		}
		var t Test
		if json.Unmarshal(data, &t) != nil {
			continue
		}

		// Check for test-specific grader, fall back to root grader
		grader := filepath.Join(testsDir, entry.Name(), "grader.py")
		if _, err := os.Stat(grader); os.IsNotExist(err) {
			grader = filepath.Join(testsDir, "grader.py")
		}

		result = append(result, TestDir{
			Test:   t,
			Dir:    filepath.Join(testsDir, entry.Name()),
			Sample: filepath.Join(testsDir, entry.Name(), "sample"),
			Grader: grader,
		})
	}

	// Sort for deterministic order
	sort.Slice(result, func(i, j int) bool {
		return result[i].Test.ID < result[j].Test.ID
	})

	return result
}

// --- Agent runner ---

func runAgent(agent Agent, td TestDir, scriptDir string) RunResult {
	result := RunResult{
		Agent:   agent.Name,
		TestID:  td.Test.ID,
		AgentID: agent.ID,
	}

	// Build command — run from /tmp so no project context leaks
	task := td.Test.Task
	cmdStr := strings.ReplaceAll(agent.CmdTpl, "{task}", task)

	// Run agent from /tmp
	cmd := exec.Command("sh", "-c", cmdStr)
	cmd.Dir = "/tmp"
	cmd.Env = os.Environ()

	var stdout, stderr bytes.Buffer
	cmd.Stdout = &stdout
	cmd.Stderr = &stderr

	err := cmd.Run()
	if err != nil {
		result.Err = err
	}

	// Extract session ID from output
	output := stdout.String() + stderr.String()
	sid := extractSessionID(output)

	// Read tokens from agent's session DB
	input, outputTokens := readTokens(agent.ID, sid)
	result.Input = input
	result.Output = outputTokens

	// Grade
	result.Passed = grade(td, scriptDir)

	return result
}

func extractSessionID(output string) string {
	for _, line := range strings.Split(output, "\n") {
		if strings.Contains(line, "Session:") {
			parts := strings.Split(line, "Session:")
			if len(parts) > 1 {
				sid := strings.TrimSpace(parts[1])
				// Take first word
				if idx := strings.Index(sid, " "); idx > 0 {
					sid = sid[:idx]
				}
				return sid
			}
		}
	}
	return ""
}

// --- Token reading ---

func readTokens(agentID, sid string) (int, int) {
	home, _ := os.UserHomeDir()
	var dbPath string
	if strings.HasPrefix(agentID, "collar") {
		dbPath = filepath.Join(home, ".dag", "state.db")
	} else {
		dbPath = filepath.Join(home, ".hermes", "state.db")
	}

	db, err := sql.Open("sqlite3", dbPath)
	if err != nil {
		return 0, 0
	}
	defer db.Close()

	var query string
	var args []interface{}
	if sid != "" {
		query = "SELECT input_tokens, output_tokens FROM sessions WHERE id = ?"
		args = []interface{}{sid}
	} else {
		query = "SELECT input_tokens, output_tokens FROM sessions ORDER BY started_at DESC LIMIT 1"
	}

	var input, output int
	err = db.QueryRow(query, args...).Scan(&input, &output)
	if err != nil {
		return 0, 0
	}
	return input, output
}

// --- Grading ---

func grade(td TestDir, scriptDir string) bool {
	// Run grader: python grader.py <sample_dir>
	cmd := exec.Command("python3", td.Grader, td.Sample)
	cmd.Dir = scriptDir
	out, err := cmd.Output()
	if err != nil {
		return false
	}

	var result map[string]interface{}
	if json.Unmarshal(out, &result) != nil {
		return false
	}

	passed, _ := result["passed"].(bool)
	return passed
}

// --- Terminal bench ---

func runTerminalBench(scriptDir string) {
	fmt.Println("\n  Terminal Bench — raw MCP query cost\n")

	dotdogSrc := filepath.Join(filepath.Dir(scriptDir), "dotdog", "packages", "dotdog", "src", "cli.ts")
	serveCmd := fmt.Sprintf("bun %s serve %s 2>/dev/null", dotdogSrc, scriptDir)

	calls := []struct {
		name    string
		payload string
	}{
		{"tools/list", `{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}`},
		{"getEntity('dogbench')", `{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"getEntity","arguments":{"name":"dogbench"}}}`},
		{"search('dog')", `{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"search","arguments":{"q":"dog"}}}`},
		{"traverse('dogbench',2)", `{"jsonrpc":"2.0","id":4,"method":"tools/call","params":{"name":"traverse","arguments":{"from":"dogbench","depth":2}}}`},
		{"summary()", `{"jsonrpc":"2.0","id":5,"method":"tools/call","params":{"name":"summary","arguments":{}}}`},
	}

	// Initialize first
	mcpCall(serveCmd, scriptDir, `{"jsonrpc":"2.0","id":0,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"bench","version":"0.1.0"}}}`)

	for _, call := range calls {
		resp := mcpCall(serveCmd, scriptDir, call.payload)
		if resp == nil {
			fmt.Printf("  %-25s no response\n", call.name)
			continue
		}
		text := extractMCPText(resp)
		fmt.Printf("  %-25s %d chars\n", call.name, len(text))
		if len(text) < 300 {
			fmt.Printf("    %s\n", text)
		} else {
			fmt.Printf("    %s...\n", text[:300])
		}
	}
	fmt.Print()
}

func mcpCall(serveCmd, cwd, payload string) map[string]interface{} {
	cmd := exec.Command("sh", "-c", serveCmd)
	cmd.Dir = cwd
	cmd.Env = os.Environ()

	stdin, _ := cmd.StdinPipe()
	stdout, _ := cmd.StdoutPipe()
	cmd.Start()

	stdin.Write([]byte(payload + "\n"))
	stdin.Close()

	scanner := bufio.NewScanner(stdout)
	for scanner.Scan() {
		line := scanner.Bytes()
		var resp map[string]interface{}
		if json.Unmarshal(line, &resp) == nil {
			cmd.Wait()
			return resp
		}
	}
	cmd.Wait()
	return nil
}

func extractMCPText(resp map[string]interface{}) string {
	result, ok := resp["result"].(map[string]interface{})
	if !ok {
		b, _ := json.Marshal(resp)
		return string(b)
	}
	// tools/list has result.tools, not result.content
	if tools, ok := result["tools"].([]interface{}); ok {
		b, _ := json.Marshal(tools)
		return string(b)
	}
	content, ok := result["content"].([]interface{})
	if !ok || len(content) == 0 {
		b, _ := json.Marshal(result)
		return string(b)
	}
	first, ok := content[0].(map[string]interface{})
	if !ok {
		b, _ := json.Marshal(content)
		return string(b)
	}
	text, _ := first["text"].(string)
	return text
}

// --- Results output ---

func writeResults(scriptDir string, results map[string]RunResult, model string) {
	r := Results{
		Timestamp: time.Now().UTC().Format(time.RFC3339),
		Model:     model,
		Runs:      results,
	}

	data, _ := json.MarshalIndent(r, "", " ")

	histPath := filepath.Join(scriptDir, "results.json")
	// Append to history
	var history []Results
	if existing, err := os.ReadFile(histPath); err == nil {
		json.Unmarshal(existing, &history)
	}
	history = append(history, r)
	if len(history) > 20 {
		history = history[len(history)-20:]
	}
	data, _ = json.MarshalIndent(history, "", " ")
	os.WriteFile(histPath, data, 0644)
}

// --- Helpers ---

func fmtInt(n int) string {
	if n == 0 {
		return "N/A"
	}
	return fmt.Sprintf("%d", n)
}

func calcCost(input, output int, model string) float64 {
	var inputRate, outputRate float64
	switch model {
	case "deepseek-v4-pro":
		inputRate = 0.50
		outputRate = 2.00
	default:
		inputRate = 1.00
		outputRate = 5.00
	}
	return (float64(input)/1e6)*inputRate + (float64(output)/1e6)*outputRate
}

func colorForAgent(id string) *color.Color {
	switch id {
	case "hermes":
		return color.New(color.FgCyan)
	case "hermes_dag":
		return color.New(color.FgMagenta)
	case "collar":
		return color.New(color.FgYellow)
	case "collar_dag":
		return color.New(color.FgGreen)
	default:
		return color.New()
	}
}
