import redis

client=redis.Redis(
    host="redis",
    port=6379,
    decode_responses=True,
)

client.set("test:redis","hello",ex=60)

print(client.get("test:redis"))
print(client.ttl("test:redis"))