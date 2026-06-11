import uuid as uuid_pkg
from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.orm import Mapped, MappedAsDataclass, mapped_column
from sqlalchemy.types import DATETIME


class UUIDMixin(MappedAsDataclass):
    """Mixin to add UUID primary key to MySQL models.

    Uses CHAR(36) instead of PostgreSQL's native UUID type.
    Server-side generation is omitted — UUID is always generated
    Python-side via uuid4() since MySQL has no gen_random_uuid()
    equivalent available across all versions.

    Attributes:
        uuid: CHAR(36) primary key with Python-side UUID4 generation.

    Example:
        ```python
        class Product(UUIDMixin, Base):
            __tablename__ = "products"
            name: Mapped[str] = mapped_column(String(100))

        product = Product(name="example")
        # product.uuid is automatically generated as a UUID4
        ```
    """

    uuid: Mapped[uuid_pkg.UUID] = mapped_column(
        String(36),
        primary_key=True,
        default=uuid_pkg.uuid4,
        init=False,
    )


class TimestampMixin(MappedAsDataclass):
    """Mixin for created_at and updated_at timestamps on MySQL models.

    Uses DATETIME instead of TIMESTAMP to avoid MySQL's TIMESTAMP
    2038 limitation and to support timezone-aware storage via
    SQLAlchemy's DateTime(timezone=True).

    Attributes:
        created_at: Datetime when the record was created.
        updated_at: Datetime when the record was last updated.

    Note:
        MySQL DATETIME does not store timezone info natively.
        Values are stored and retrieved as-is. Always write UTC
        explicitly (default_factory enforces this).

    Example:
        ```python
        class Product(TimestampMixin, Base):
            __tablename__ = "products"
            name: Mapped[str] = mapped_column(String(100))

        product = Product(name="example")
        # product.created_at and product.updated_at set to UTC now
        ```
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(),
        default_factory=lambda: datetime.now(UTC).replace(tzinfo=None),
        nullable=False,
        init=False,
    )

    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(),
        default_factory=lambda: datetime.now(UTC).replace(tzinfo=None),
        nullable=True,
        init=False,
    )


class SoftDeleteMixin(MappedAsDataclass):
    """Mixin to add soft delete functionality to MySQL models.

    Uses DATETIME instead of TIMESTAMP for the deleted_at field
    to avoid the 2038 limitation present in MySQL TIMESTAMP columns.

    Attributes:
        deleted_at: Datetime when the record was soft deleted.
        is_deleted: Boolean flag indicating if the record is deleted.

    Example:
        ```python
        class Product(SoftDeleteMixin, Base):
            __tablename__ = "products"
            name: Mapped[str] = mapped_column(String(100))

        product = Product(name="example")

        # Soft delete
        product.deleted_at = datetime.now(UTC).replace(tzinfo=None)
        product.is_deleted = True

        # Query active records
        active = session.query(Product).filter(Product.is_deleted == False)
        ```
    """

    deleted_at: Mapped[datetime | None] = mapped_column(
        DATETIME(),
        nullable=True,
        init=False,
    )
    is_deleted: Mapped[bool] = mapped_column(
        Boolean(),
        default=False,
        init=False,
    )