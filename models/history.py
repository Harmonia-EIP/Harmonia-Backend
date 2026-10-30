from sqlalchemy import JSON, Column, DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.sql import func

from database.base import Base


class History(Base):
    __tablename__ = "history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    name = Column(String(1000), nullable=False)
    type = Column(String(10), nullable=False)  # 'generate' | 'refine'
    parameters = Column(JSON, nullable=False)  # {nom_param: valeur}
    model_id = Column(String(100), nullable=True)  # modèle IA demandé (id)
    model_name = Column(String(200), nullable=True)  # modèle IA demandé (nom)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    last_used_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (Index("idx_history_user_last_used", "user_id", "last_used_at"),)