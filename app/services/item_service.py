"""Service de gestion de la logique métier des articles.

Ce module contient la couche service qui encapsule toutes les
opérations CRUD (Create, Read, Update, Delete) sur les articles.
"""

from sqlmodel import Session, select
import logging

from app.database import engine as _engine
from typing import cast
from app.models.item import Item
from app.schemas.item import ItemCreate, ItemUpdate


class ItemService:
    """Service gérant les opérations métier sur les articles.

    Cette classe fournit des méthodes statiques pour effectuer
    toutes les opérations CRUD sur les articles, en séparant
    la logique métier des routes API.
    """

    @staticmethod
    def get_all(db: Session, skip: int = 0, limit: int = 100) -> list[Item]:
        """Récupère une liste paginée d'articles.

        Args:
            db: Session de base de données active.
            skip: Nombre d'articles à sauter (pour pagination). Par défaut 0.
            limit: Nombre maximum d'articles à retourner. Par défaut 100.

        Returns:
            Liste d'objets Item de la base de données.

        Example:
            >>> items = ItemService.get_all(db, skip=0, limit=10)
            >>> len(items)  # Maximum 10 articles
        """
        statement = select(Item).offset(skip).limit(limit)
        result = db.exec(statement)
        # Return value is Any; cast to the concrete type for mypy
        return cast(list[Item], result.all())

    @staticmethod
    def get_by_id(db: Session, item_id: int) -> Item | None:
        """Récupère un article par son identifiant.

        Args:
            db: Session de base de données active.
            item_id: Identifiant unique de l'article à récupérer.

        Returns:
            L'objet Item correspondant, ou None si non trouvé.

        Example:
            >>> item = ItemService.get_by_id(db, 1)
            >>> if item:
            ...     print(item.nom)
        """
        return db.get(Item, item_id)

    @staticmethod
    def create(db: Session, item_data: ItemCreate) -> Item:
        """Crée un nouvel article dans la base de données.

        Args:
            db: Session de base de données active.
            item_data: Données validées pour créer l'article (schéma ItemCreate).

        Returns:
            L'objet Item nouvellement créé avec son ID généré.

        Example:
            >>> new_item = ItemCreate(nom="Écran", prix=299.99)
            >>> created = ItemService.create(db, new_item)
            >>> print(created.id)  # ID auto-généré
        """
        logger = logging.getLogger("service.item")
        item = Item(**item_data.model_dump())
        db.add(item)
        try:
            db.commit()
            db.refresh(item)
            logger.info(
                "Created item id=%s name=%s", item.id, getattr(item, "nom", "<unknown>")
            )
            return item
        except Exception as exc:  # pragma: no cover - DB error handling
            logger.error("Failed to persist new item: %s", exc)
            # Attempt to rollback to avoid leaving the session in a bad state
            try:
                db.rollback()
            except Exception:
                logger.debug("Rollback failed after create error")
            raise

    @staticmethod
    def update(db: Session, item_id: int, item_data: ItemUpdate) -> Item | None:
        """Met à jour un article existant avec les données fournies.

        Effectue une mise à jour partielle en ne modifiant que les champs
        fournis dans item_data (grâce à exclude_unset=True).

        Args:
            db: Session de base de données active.
            item_id: Identifiant de l'article à mettre à jour.
            item_data: Données de mise à jour (schéma ItemUpdate).

        Returns:
            L'objet Item mis à jour, ou None si l'article n'existe pas.

        Example:
            >>> update_data = ItemUpdate(prix=249.99)  # Ne met à jour que le prix
            >>> updated = ItemService.update(db, 1, update_data)
        """
        logger = logging.getLogger("service.item")
        item = db.get(Item, item_id)
        if not item:
            return None

        update_data = item_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(item, field, value)

        try:
            db.add(item)
            db.commit()
            db.refresh(item)
            logger.info("Updated item id=%s", item_id)
            return item
        except Exception as exc:  # pragma: no cover - DB error handling
            logger.error("Failed to update item id=%s: %s", item_id, exc)
            try:
                db.rollback()
            except Exception:
                logger.debug("Rollback failed after update error")
            raise

    @staticmethod
    def delete(db: Session, item_id: int) -> bool:
        """Supprime un article de la base de données.

        Args:
            db: Session de base de données active.
            item_id: Identifiant de l'article à supprimer.

        Returns:
            True si l'article a été supprimé, False s'il n'existait pas.

        Example:
            >>> success = ItemService.delete(db, 1)
            >>> if success:
            ...     print("Article supprimé avec succès")
        """
        logger = logging.getLogger("service.item")
        item = db.get(Item, item_id)
        if not item:
            return False
        try:
            db.delete(item)
            db.commit()
            logger.info("Deleted item id=%s", item_id)
            return True
        except Exception as exc:  # pragma: no cover - DB error handling
            logger.error("Failed to delete item id=%s: %s", item_id, exc)
            try:
                db.rollback()
            except Exception:
                logger.debug("Rollback failed after delete error")
            raise
