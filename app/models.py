"""Database schema for the Examination Management Portal."""

from datetime import datetime, timezone

from werkzeug.security import generate_password_hash

from app import db


class User(db.Model):
    __tablename__ = "users"
    __table_args__ = (
        db.CheckConstraint(
            "role IN ('admin', 'examiner', 'student')", name="ck_users_role"
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, index=True)
    full_name = db.Column(db.String(160), nullable=False)
    phone = db.Column(db.String(40))
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False,
                           default=lambda: datetime.now(timezone.utc))

    examiner_profile = db.relationship(
        "ExaminerProfile", back_populates="user", uselist=False,
        cascade="all, delete-orphan"
    )
    student_bookings = db.relationship(
        "Booking", back_populates="student",
        foreign_keys="Booking.student_id"
    )

    @classmethod
    def create_admin(cls, email, password, full_name="System Administrator"):
        """Create the single preconfigured administrator, idempotently."""
        existing_admin = db.session.scalar(
            db.select(cls).where(cls.role == "admin")
        )
        if existing_admin:
            return existing_admin, False

        admin = cls(
            email=email.strip().lower(),
            password_hash=generate_password_hash(password),
            role="admin",
            full_name=full_name.strip(),
        )
        db.session.add(admin)
        db.session.commit()
        return admin, True


class Course(db.Model):
    __tablename__ = "courses"

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(30), nullable=False, unique=True, index=True)
    name = db.Column(db.String(160), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(20), nullable=False, default="active")
    created_at = db.Column(db.DateTime(timezone=True), nullable=False,
                           default=lambda: datetime.now(timezone.utc))

    examinations = db.relationship(
        "Examination", back_populates="course", cascade="all, delete-orphan"
    )


class Examination(db.Model):
    __tablename__ = "examinations"
    __table_args__ = (
        db.CheckConstraint(
            "status IN ('draft', 'slot_creation', 'booking_open', 'closed', 'completed')",
            name="ck_examinations_status",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey("courses.id"), nullable=False,
                          index=True)
    name = db.Column(db.String(180), nullable=False)
    exam_type = db.Column(db.String(40), nullable=False)
    duration_minutes = db.Column(db.Integer, nullable=False)
    maximum_marks = db.Column(db.Numeric(7, 2), nullable=False)
    slot_creation_start = db.Column(db.DateTime(timezone=True))
    slot_creation_end = db.Column(db.DateTime(timezone=True))
    booking_start = db.Column(db.DateTime(timezone=True))
    booking_end = db.Column(db.DateTime(timezone=True))
    status = db.Column(db.String(30), nullable=False, default="draft", index=True)
    instructions = db.Column(db.Text)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False,
                           default=lambda: datetime.now(timezone.utc))

    course = db.relationship("Course", back_populates="examinations")
    rubrics = db.relationship(
        "ExaminationRubric", back_populates="examination",
        cascade="all, delete-orphan"
    )
    slots = db.relationship(
        "ExaminationSlot", back_populates="examination",
        cascade="all, delete-orphan"
    )
    bookings = db.relationship("Booking", back_populates="examination")


class ExaminationRubric(db.Model):
    __tablename__ = "examination_rubrics"

    id = db.Column(db.Integer, primary_key=True)
    examination_id = db.Column(db.Integer, db.ForeignKey("examinations.id"),
                               nullable=False, index=True)
    criterion_name = db.Column(db.String(160), nullable=False)
    maximum_marks = db.Column(db.Numeric(7, 2), nullable=False)
    weightage = db.Column(db.Numeric(5, 2), nullable=False, default=0)
    description = db.Column(db.Text)
    position = db.Column(db.Integer, nullable=False, default=0)

    examination = db.relationship("Examination", back_populates="rubrics")


class ExaminerProfile(db.Model):
    __tablename__ = "examiner_profiles"

    id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"),
                   primary_key=True)
    department = db.Column(db.String(120))
    contact_details = db.Column(db.Text)
    status = db.Column(db.String(20), nullable=False, default="pending")

    user = db.relationship("User", back_populates="examiner_profile")
    slots = db.relationship("ExaminationSlot", back_populates="examiner")


class ExaminationSlot(db.Model):
    __tablename__ = "examination_slots"
    __table_args__ = (
        db.CheckConstraint(
            "status IN ('available', 'full', 'cancelled', 'completed')",
            name="ck_examination_slots_status",
        ),
        db.CheckConstraint("capacity > 0", name="ck_examination_slots_capacity"),
    )

    id = db.Column(db.Integer, primary_key=True)
    examination_id = db.Column(db.Integer, db.ForeignKey("examinations.id"),
                               nullable=False, index=True)
    examiner_id = db.Column(db.Integer,
                            db.ForeignKey("examiner_profiles.id", ondelete="RESTRICT"),
                            nullable=False, index=True)
    starts_at = db.Column(db.DateTime(timezone=True), nullable=False, index=True)
    ends_at = db.Column(db.DateTime(timezone=True), nullable=False)
    capacity = db.Column(db.Integer, nullable=False)
    available_seats = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), nullable=False, default="available", index=True)
    meeting_link = db.Column(db.String(500))

    examination = db.relationship("Examination", back_populates="slots")
    examiner = db.relationship("ExaminerProfile", back_populates="slots")
    bookings = db.relationship("Booking", back_populates="slot")


class Booking(db.Model):
    __tablename__ = "bookings"
    __table_args__ = (
        db.UniqueConstraint("student_id", "examination_id",
                            name="uq_booking_student_examination"),
        db.CheckConstraint(
            "status IN ('booked', 'cancelled', 'completed')",
            name="ck_bookings_status",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="RESTRICT"),
                           nullable=False, index=True)
    slot_id = db.Column(db.Integer, db.ForeignKey("examination_slots.id"),
                        nullable=False, index=True)
    # Kept on Booking so SQLite can enforce one booking per student/exam.
    examination_id = db.Column(db.Integer, db.ForeignKey("examinations.id"),
                               nullable=False, index=True)
    booked_at = db.Column(db.DateTime(timezone=True), nullable=False,
                          default=lambda: datetime.now(timezone.utc))
    status = db.Column(db.String(20), nullable=False, default="booked", index=True)

    student = db.relationship("User", back_populates="student_bookings",
                              foreign_keys=[student_id])
    slot = db.relationship("ExaminationSlot", back_populates="bookings")
    examination = db.relationship("Examination", back_populates="bookings")
    evaluation = db.relationship("Evaluation", back_populates="booking", uselist=False,
                                 cascade="all, delete-orphan")


class Evaluation(db.Model):
    __tablename__ = "evaluations"

    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey("bookings.id", ondelete="CASCADE"),
                           nullable=False, unique=True, index=True)
    student_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False,
                           index=True)
    examiner_id = db.Column(db.Integer, db.ForeignKey("examiner_profiles.id"),
                            nullable=False, index=True)
    total_marks = db.Column(db.Numeric(7, 2))
    remarks = db.Column(db.Text)
    evaluated_at = db.Column(db.DateTime(timezone=True))
    status = db.Column(db.String(20), nullable=False, default="pending")

    booking = db.relationship("Booking", back_populates="evaluation")
    student = db.relationship("User", foreign_keys=[student_id])
    examiner = db.relationship("ExaminerProfile", foreign_keys=[examiner_id])

