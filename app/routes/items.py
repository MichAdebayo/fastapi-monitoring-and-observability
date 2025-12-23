from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlmodel import Session
from typing import List
import logging


from app.database import get_db
from app.schemas.item import ItemCreate, ItemResponse, ItemUpdate
from app.services.item_service import ItemService
from app.models.item import Item
from app.monitoring.metrics import (
    items_created_total,
    items_read_total,
    target_item_read_total,
    items_updated_total,
    items_deleted_total,
    DatabaseQueryTimer,
)

router = APIRouter(prefix="/items", tags=["items"])

MAX_ITEMS_PER_PAGE = 1000

logger = logging.getLogger("api")


@router.get("/", response_model=List[ItemResponse])
def get_items(
    skip: int = 0, limit: int = 100, db: Session = Depends(get_db)
) -> List[Item]:
    """Get a list of items with pagination."""
    # Validate pagination params and enforce sensible caps
    if skip < 0:
        logger.warning("Negative skip adjusted to 0 (was=%s)", skip)
        skip = 0
    if limit <= 0:
        logger.warning("Non-positive limit adjusted to 1 (was=%s)", limit)
        limit = 1
    if limit > MAX_ITEMS_PER_PAGE:
        logger.warning(
            "Limit too large; capped to %s (requested=%s)", MAX_ITEMS_PER_PAGE, limit
        )
        limit = MAX_ITEMS_PER_PAGE

    with DatabaseQueryTimer():
        items = ItemService.get_all(db, skip, limit)

    items_read_total.inc(len(items))
    logger.info("Fetched %d items (skip=%s limit=%s)", len(items), skip, limit)
    return items


@router.post("/", response_model=ItemResponse, status_code=status.HTTP_201_CREATED)
def create_item(
    item_data: ItemCreate = Body(...), db: Session = Depends(get_db)
) -> Item:
    """Creates a new item in the database.

    Accepts item data and stores the new item, returning the created item.

    Args:
        item_data (ItemCreate): The data for the item to create.
        db (Session): The database session dependency.

    Returns:
        ItemResponse: The created item.
    """
    logger.info(
        "Create item request received: name=%s", getattr(item_data, "nom", "<unknown>")
    )
    with DatabaseQueryTimer():
        try:
            created = ItemService.create(db, item_data)
            # increment metric only on successful persistence
            items_created_total.inc()
            logger.info(
                "Item created successfully id=%s name=%s",
                created.id,
                getattr(created, "nom", "<unknown>"),
            )
            return created
        except Exception as exc:
            logger.error("Failed to create item: %s", exc)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create item",
            ) from exc


@router.get("/{item_id}", response_model=ItemResponse)
def get_item(item_id: int, db: Session = Depends(get_db)) -> Item:
    """Retrieves a single item by its ID.

    Returns the item if found, otherwise raises a 404 error.

    Args:
        item_id (int): The ID of the item to retrieve.
        db (Session): The database session dependency.

    Returns:
        ItemResponse: The requested item.

    Raises:
        HTTPException: If the item is not found.
    """
    with DatabaseQueryTimer():
        if item := ItemService.get_by_id(db, item_id):
            logger.info("Item retrieved id=%s", item_id)
            target_item_read_total.inc()
            return item
        else:
            logger.warning("Item not found id=%s", item_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Item with id {item_id} not found",
            ) from None


@router.put("/{item_id}", response_model=ItemResponse)
def update_item(
    item_id: int, item_data: ItemUpdate = Body(...), db: Session = Depends(get_db)
) -> Item:
    """Updates an existing item with new data.

    Returns the updated item if found, otherwise raises a 404 error.

    Args:
        item_id (int): The ID of the item to update.
        item_data (ItemUpdate): The new data for the item.
        db (Session): The database session dependency.

    Returns:
        ItemResponse: The updated item.

    Raises:
        HTTPException: If the item is not found.
    """
    logger.info(
        "Update request for id=%s data=%s",
        item_id,
        item_data.model_dump(exclude_unset=True),
    )
    with DatabaseQueryTimer():
        if item := ItemService.update(db, item_id, item_data):
            logger.info("Item updated id=%s", item_id)
            items_updated_total.inc()
            return item
        else:
            logger.warning("Update failed - not found id=%s", item_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Item with id {item_id} not found",
            ) from None


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(item_id: int, db: Session = Depends(get_db)) -> None:
    """Deletes an item by its ID.

    Removes the item from the database if it exists, otherwise raises a 404 error.

    Args:
        item_id (int): The ID of the item to delete.
        db (Session): The database session dependency.

    Raises:
        HTTPException: If the item is not found.
    """
    logger.info("Delete request for id=%s", item_id)

    with DatabaseQueryTimer():
        deleted = ItemService.delete(db, item_id)
    if deleted:
        logger.info("Item deleted id=%s", item_id)
        items_deleted_total.inc()
        return None
    else:
        logger.warning("Delete failed - not found id=%s", item_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item with id {item_id} not found",
        ) from None
