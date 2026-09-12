from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.models import Report, ReportUpdate, Zone, Need, Resource, Allocation, Agency
from app.schemas.schemas import ReportCreate, ReportStatusUpdate
from app.agents.need_assessment_agent import need_assessment_agent

class ReportService:
    @staticmethod
    def get_all_reports(db: Session, limit: int = 100, status_filter: Optional[str] = None) -> List[Report]:
        query = db.query(Report)
        if status_filter:
            query = query.filter(Report.status == status_filter)
        return query.order_by(Report.created_at.desc()).limit(limit).all()

    @staticmethod
    def get_report_by_id(db: Session, report_id: str) -> Optional[Report]:
        return db.query(Report).filter(Report.id == report_id).first()

    @staticmethod
    def create_report(db: Session, report_in: ReportCreate) -> Report:
        # If zone_id not provided, assign to nearest zone
        zone_id = report_in.zone_id
        if not zone_id:
            # find closest zone by simple distance
            zones = db.query(Zone).all()
            if zones:
                best_z = min(
                    zones,
                    key=lambda z: (z.latitude - report_in.latitude) ** 2 + (z.longitude - report_in.longitude) ** 2
                )
                zone_id = best_z.id

        # Normalize incoming report dict
        raw_dict = report_in.dict() if hasattr(report_in, "dict") else report_in.model_dump()

        # Execute Need & Assessment Agent (pure & stateless)
        assessment = need_assessment_agent.assess_incident(raw_dict, input_mode="REPORT")
        assessment_dict = assessment.dict() if hasattr(assessment, "dict") else assessment.model_dump()

        # Use normalized disaster type and counts if provided
        d_type = report_in.disaster_type or (assessment.disaster.type if assessment and assessment.disaster else None) or "Emergency Incident"
        
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

        # Execute Priority & Severity Agent
        try:
            from app.agents.priority_severity_agent import priority_severity_agent
            priority_assessment = priority_severity_agent.score_incident(assessment)
        except Exception:
            priority_assessment = None

        priority_dict = (
            priority_assessment.dict() if hasattr(priority_assessment, "dict") else priority_assessment.model_dump()
        ) if priority_assessment else None
        prio_score = priority_assessment.zone_score if priority_assessment else 7.5
        prio_lvl = priority_assessment.priority_level if priority_assessment else "HIGH"
        prio_ver = priority_assessment.scoring_version if priority_assessment else "1.0"

        location_txt = report_in.location_text or f"{report_in.latitude:.4f}°, {report_in.longitude:.4f}°"
        rep_name = report_in.reporter_name or "Citizen Reporter"

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
            reporter_name=rep_name,
            reporter_phone=report_in.reporter_phone,
            location_text=location_txt,
            admin_notes=report_in.admin_notes,
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

    @staticmethod
    def update_report_status(
        db: Session,
        report_id: str,
        new_status: str,
        notes: Optional[str] = None,
        actor: str = "Command Administrator",
    ) -> Optional[Report]:
        report = db.query(Report).filter(Report.id == report_id).first()
        if not report:
            return None

        old_status = report.status
        report.status = new_status
        if notes:
            existing = report.admin_notes or ""
            timestamp_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
            report.admin_notes = f"{existing}\n[{timestamp_str} by {actor}]: {notes}".strip()

        # Add ReportUpdate history log
        update_record = ReportUpdate(
            report_id=report.id,
            status_change=f"{old_status} -> {new_status}",
            notes=notes,
            updated_by=actor,
        )
        db.add(update_record)
        db.commit()
        db.refresh(report)
        return report

    @staticmethod
    def accept_report(
        db: Session,
        report_id: str,
        notes: Optional[str] = None,
        actor: str = "Command Administrator",
    ) -> Optional[Report]:
        """Marks report as VERIFIED / ACCEPTED and creates or updates active need manifest."""
        report = ReportService.update_report_status(db, report_id, "VERIFIED", notes=notes or "Incident verified and accepted by administrator.", actor=actor)
        if report and report.zone_id:
            # Create a need in the zone if not already present
            existing_need = db.query(Need).filter(Need.zone_id == report.zone_id, Need.status != "FULFILLED").first()
            if not existing_need:
                new_need = Need(
                    zone_id=report.zone_id,
                    resource_type=report.disaster_type or "General Relief",
                    quantity_required=max(1, (report.people_affected or 1) // 5 + 1),
                    quantity_fulfilled=0,
                    severity=report.priority_score or 8.0,
                    priority_score=report.priority_score or 8.0,
                    status="CRITICAL",
                )
                db.add(new_need)
                db.commit()
        return report

    @staticmethod
    def dispatch_report(
        db: Session,
        report_id: str,
        agency_id: Optional[str] = None,
        resource_id: Optional[str] = None,
        notes: Optional[str] = None,
        actor: str = "Command Administrator",
    ) -> Optional[Report]:
        """Dispatches emergency response units to this report location."""
        report = ReportService.update_report_status(db, report_id, "ACTIONED", notes=notes or "Emergency response units dispatched to location.", actor=actor)
        if report and report.zone_id:
            # Allocate available resource if found
            available_res = db.query(Resource).filter(Resource.status == "AVAILABLE").first()
            if available_res:
                available_res.status = "ALLOCATED"
                alloc = Allocation(
                    resource_id=available_res.id,
                    zone_id=report.zone_id,
                    quantity=1,
                    status="EN_ROUTE",
                    distance_km=3.5,
                    eta_minutes=9,
                )
                db.add(alloc)
                db.commit()
        return report

    @staticmethod
    def resolve_report(
        db: Session,
        report_id: str,
        notes: Optional[str] = None,
        actor: str = "Command Administrator",
    ) -> Optional[Report]:
        """Marks report as RESOLVED."""
        return ReportService.update_report_status(db, report_id, "RESOLVED", notes=notes or "Incident resolved on ground.", actor=actor)

    @staticmethod
    def dismiss_report(
        db: Session,
        report_id: str,
        notes: Optional[str] = None,
        actor: str = "Command Administrator",
    ) -> Optional[Report]:
        """Marks report as DISMISSED / REJECTED."""
        return ReportService.update_report_status(db, report_id, "DISMISSED", notes=notes or "Report dismissed by administrator.", actor=actor)

    @staticmethod
    def delete_report(db: Session, report_id: str) -> bool:
        report = db.query(Report).filter(Report.id == report_id).first()
        if not report:
            return False
        db.delete(report)
        db.commit()
        return True

report_service = ReportService()
