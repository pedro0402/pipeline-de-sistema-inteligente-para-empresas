from sqlalchemy import CheckConstraint, Column, DateTime, ForeignKey, Integer, Text, func

from core.database import Base


class OpportunityAnalysis(Base):
    __tablename__ = "opportunity_analysis"

    id = Column(Integer, primary_key=True)
    opportunity_id = Column(
        Integer,
        ForeignKey("opportunities.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    summary = Column(Text)
    relevance_score = Column(Integer)
    recommended_action = Column(Text)
    analyzed_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        CheckConstraint(
            "relevance_score >= 0 AND relevance_score <= 10",
            name="ck_opportunity_analysis_relevance_score",
        ),
    )
