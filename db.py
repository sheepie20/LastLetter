from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, Integer, BigInteger, String

DATABASE_URL = "sqlite+aiosqlite:///./lastletter.db"

engine = create_async_engine(DATABASE_URL)
SessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

Base = declarative_base()

# Example model: stores which channel is set up for the bot in each guild
class GuildConfig(Base):
    __tablename__ = "guild_configs"
    id = Column(Integer, primary_key=True, index=True)
    guild_id = Column(BigInteger, unique=True, index=True, nullable=False)
    channel_id = Column(BigInteger, nullable=False)

class Words(Base):
    __tablename__ = "words"
    id = Column(Integer, primary_key=True, index=True)
    word = Column(String, unique=True, nullable=False, index=True)
    author_id = Column(BigInteger, nullable=True)  # Optionally track who submitted the word
    guild_id = Column(BigInteger, nullable=True)   # Optionally track which guild the word was used in
