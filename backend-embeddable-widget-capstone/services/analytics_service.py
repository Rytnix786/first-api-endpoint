# services/analytics_service.py — Owner Dashboard Analytics

from sqlalchemy.orm import Session
from sqlalchemy import func
from models import Widget, Submission
from typing import Dict, Any, List


class AnalyticsService:
    @staticmethod
    def get_tenant_stats(db: Session, tenant_id: str) -> Dict[str, Any]:
        total_widgets = db.query(func.count(Widget.id)).filter(Widget.tenant_id == tenant_id).scalar() or 0
        total_submissions = db.query(func.count(Submission.id)).filter(
            Submission.tenant_id == tenant_id,
            Submission.is_spam == False
        ).scalar() or 0
        spam_blocked = db.query(func.count(Submission.id)).filter(
            Submission.tenant_id == tenant_id,
            Submission.is_spam == True
        ).scalar() or 0

        recent_submissions = db.query(Submission).filter(
            Submission.tenant_id == tenant_id,
            Submission.is_spam == False
        ).order_by(Submission.created_at.desc()).limit(10).all()

        recent_list = [
            {
                "id": s.id,
                "widget_id": s.widget_id,
                "name": s.name,
                "email": s.email,
                "country": s.country,
                "city": s.city,
                "created_at": s.created_at.isoformat()
            }
            for s in recent_submissions
        ]

        return {
            "tenant_id": tenant_id,
            "total_widgets": total_widgets,
            "total_submissions": total_submissions,
            "spam_blocked_count": spam_blocked,
            "recent_submissions": recent_list
        }

    @staticmethod
    def get_geo_breakdown(db: Session, tenant_id: str) -> Dict[str, Any]:
        country_counts = db.query(
            Submission.country, func.count(Submission.id)
        ).filter(
            Submission.tenant_id == tenant_id,
            Submission.is_spam == False,
            Submission.country != None
        ).group_by(Submission.country).all()

        country_dict = {country: count for country, count in country_counts}

        top_cities = db.query(
            Submission.city, Submission.country, func.count(Submission.id).label("count")
        ).filter(
            Submission.tenant_id == tenant_id,
            Submission.is_spam == False,
            Submission.city != None
        ).group_by(Submission.city, Submission.country).order_by(func.count(Submission.id).desc()).limit(5).all()

        city_list = [{"city": city, "country": country, "count": count} for city, country, count in top_cities]

        return {
            "tenant_id": tenant_id,
            "country_breakdown": country_dict,
            "top_cities": city_list
        }
