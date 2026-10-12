from sqlalchemy import CheckConstraint, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from database.base import Base

PALETTE_SIZE = 3
DEFAULT_PALETTE = ["#00D4FF", "#7B8CFF", "#9AA5B8"]
DEFAULT_LAST_COLOR_ID = 1

def build_palette(*colors: str) -> list[dict]:
    """[{"id": 1, "color": "#..."}, {"id": 2, ...}, {"id": 3, ...}]"""
    return [{"id": i + 1, "color": c} for i, c in enumerate(colors)]


class UserParams(Base):
    __tablename__ = "user_params"

    DEFAULT_PALETTE = DEFAULT_PALETTE
    
    __table_args__ = (
        CheckConstraint(
            f"last_color_id >= 1 AND last_color_id <= {PALETTE_SIZE}",
            name="ck_user_params_last_color_id",
        ),
    )

    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )

    # Palette de base : 3 couleurs hex "#RRGGBB" (ids 1, 2, 3)
    color_1 = Column(String(7), nullable=False, default=DEFAULT_PALETTE[0])
    color_2 = Column(String(7), nullable=False, default=DEFAULT_PALETTE[1])
    color_3 = Column(String(7), nullable=False, default=DEFAULT_PALETTE[2])

    # Id (1, 2 ou 3) de la dernière couleur sélectionnée : on rouvre dessus
    last_color_id = Column(Integer, nullable=False, default=DEFAULT_LAST_COLOR_ID)

    user = relationship("User", back_populates="params")

    @property
    def palette(self) -> list[dict]:
        return build_palette(self.color_1, self.color_2, self.color_3)

    def set_color(self, color_id: int, color: str) -> None:
        setattr(self, f"color_{color_id}", color)