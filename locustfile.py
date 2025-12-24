from locust import HttpUser, task, between
import random
import os
import time


class ItemsAPIUser(HttpUser):
    """Utilisateur complet - Opérations CRUD"""

    wait_time = between(0.1, 0.5)
    item_ids = []

    def on_start(self):
        if auth_token := os.getenv("AUTH_TOKEN"):
            self.client.headers = {"Authorization": f"Bearer {auth_token}"}
        for i in range(3):
            response = self.client.post(
                "/items/",
                json={
                    "nom": f"Initial Item {i}",
                    "prix": round(random.uniform(10, 100), 2),
                },
            )
            if response.status_code == 201:
                data = response.json()
                self.item_ids.append(data["id"])

    @task(5)
    def list_items(self):
        time.sleep(0.2)
        self.client.get("/items/")

    @task(3)
    def get_item(self):
        if self.item_ids:
            item_id = random.choice(self.item_ids)
            time.sleep(0.5)
            self.client.get(f"/items/{item_id}/", name="/items/{id}")

    @task(2)
    def create_item(self):
        response = self.client.post(
            "/items/",
            json={
                "nom": f"Item {random.randint(1, 10000)}",
                "prix": round(random.uniform(10, 1000), 2),
            },
        )
        if response.status_code == 201:
            data = response.json()
            self.item_ids.append(data["id"])

    @task(1)
    def update_item(self):
        if self.item_ids:
            item_id = random.choice(self.item_ids)
            time.sleep(0.5)
            self.client.put(
                f"/items/{item_id}/",
                json={
                    "nom": f"Updated {random.randint(1, 10000)}",
                    "prix": round(random.uniform(10, 1000), 2),
                },
                name="/items/{id}",
            )

    @task(1)
    def delete_item(self):
        if len(self.item_ids) > 10:
            item_id = self.item_ids.pop()
            self.client.delete(f"/items/{item_id}/", name="/items/{id}")


class LightUser(HttpUser):
    """Utilisateur léger - Lecture seule"""

    wait_time = between(2, 5)

    def on_start(self):
        if auth_token := os.getenv("AUTH_TOKEN"):
            self.client.headers = {"Authorization": f"Bearer {auth_token}"}

    @task(10)
    def read_items(self):
        self.client.get("/items/")

    @task(5)
    def read_single_item(self):
        item_id = random.randint(1, 50)
        self.client.get(f"/items/{item_id}/", name="/items/{id}")
