import redis
from decouple import config

client=redis.Redis(
    host=config("REDIS_HOST",default="127.0.0.1"),
    port=config("REDIS_PORT",cast=int,default=6379),
    decode_responses=True,
)

# client.set("test:redis","hello",ex=60)

# print(client.get("test:redis"))
# print(client.ttl("test:redis"))