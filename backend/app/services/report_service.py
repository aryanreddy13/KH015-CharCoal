from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.models import Report, Zone
from app.schemas.schemas import ReportCreate
from app.agents.need_assessment_agent import need_assessment_agent

class ReportService:
    @staticmethod
    def get_all_reports(db: Session, limit: int = 100) -> List[Report]:
        return db.query(Report).order_by(Report.created_at.desc()).limit(limit).all()

    @staticmethod
    def create_report(db: Session, report_in: ReportCreate) -> Report:
        # If zone_id not provided, assign to nearest zone or highest severity zone for Phase 1
        zone_id = report_in.zone_id
        if not zone_id:
            # find closest or default to Zone A
            first_zone = db.query(Zone).first()
            if first_zone:
                zone_id = first_zone.id

        # Normalize incoming report dict
        raw_dict = report_in.dict() if hasattr(report_in, "dict") else report_in.model_dump()

        # Execute Need & Assessment Agent (pure & stateless)
        assessment = need_assessment_agent.assess_incident(raw_dict, input_mode="REPORT")
        assessment_dict = assessment.dict() if hasattr(assessment, "dict") else assessment.model_dump()

        # Use normalized disaster type and counts if provided
        d_type = report_in.disaster_type or (assessment.disaster.type if assessment and assessment.disaster else None) or "Emergency Report"
        
        def get_val(f_num, default):
            if f_num is None:
                return default
            if hasattr(f_num, "value"):
                return f_num.value if f_num.value is not None else default
            if isinstance(f_num, dict):
                return f_num.get("value", default)
            return f_num

        aff = report_in.people_affected if report_in.people_affected is not None else get_val(assessment.people.affected, 1)
        inj = report_in.injured_people if report_in.injured_people is not None else get_val(assessment.people.injured, 0)
        mis = report_in.missing_people if report_in.missing_people is not None else get_val(assessment.people.missing, 0)

        # Execute Priority & Severity Agent (pure & stateless scoring layer)
        try:
            from app.agents.priority_severity_agent import priority_severity_agent
            priority_assessment = priority_severity_agent.score_incident(assessment)
        except Exception as prio_err:
            priority_assessment = None

        priority_dict = (
            priority_assessment.dict() if hasattr(priority_assessment, "dict") else priority_assessment.model_dump()
        ) if priority_assessment else None
        prio_score = priority_assessment.zone_score if priority_assessment else None
        prio_lvl = priority_assessment.priority_level if priority_assessment else None
        prio_ver = priority_assessment.scoring_version if priority_assessment else "1.0"

        report = Report(
            zone_id=zone_id,
            reporter_id=report_in.reporter_id,
            disaster_type=d_type,
            description=report_in.description or "",
            people_affected=aff,
            injured_people=inj,
            missing_people=mis,
            latitude=report_in.latitude,
            longitude=report_in.longitude,
            photo_url=report_in.photo_url,
            status=report_in.status or "PENDING REVIEW",
            assessment_json=assessment_dict,
            assessment_version=assessment.extraction_metadata.version,
            assessment_status="COMPLETED",
            priority_assessment_json=priority_dict,
            priority_score=prio_score,
            priority_level=prio_lvl,
            priority_scoring_version=prio_ver,
        )
        db.add(report)
        db.commit()
        db.refresh(report)
        return report

report_service = ReportService()
