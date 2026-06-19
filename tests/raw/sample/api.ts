type User = { id: number; name: string; email: string };

async function fetchUser(id: number): Promise<User> {
  const res = await fetch(`/users/${id}`);
  return res.json();
}

async function createUser(data: Omit<User, "id">): Promise<User> {
  const res = await fetch("/users", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  return res.json();
}

export { fetchUser, createUser };
