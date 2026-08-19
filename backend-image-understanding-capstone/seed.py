# seed.py — Database Seeding Script with Categorized Image Corpus and Blog Posts

import logging
from datetime import datetime, timezone
from database import SessionLocal, init_db
from models import ImageItem, BlogPost, CostLog
from services.embedding_service import EmbeddingService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SeedScript")

# Curated image corpus for the Image Understanding & Matching Engine
IMAGE_CORPUS = [
    {
        "id": "img_fox_01",
        "filename": "red_fox_autumn_forest.jpg",
        "url": "https://images.unsplash.com/photo-1474511320723-9a56873867b5",
        "subject": "red fox",
        "category": "animal",
        "attributes": ["orange fur", "wild", "forest", "bushy tail"],
        "caption": "A vibrant red fox standing alert in an autumn forest with colorful foliage.",
        "confidence": 0.94
    },
    {
        "id": "img_fox_02",
        "filename": "vulpes_vulpes_kit.jpg",
        "url": "https://images.unsplash.com/photo-1516934024742-b461fba47600",
        "subject": "red fox",
        "category": "animal",
        "attributes": ["young kit", "wildlife", "meadow", "vulpes"],
        "caption": "A young Vulpes vulpes kit playing in a sunny green meadow.",
        "confidence": 0.91
    },
    {
        "id": "img_wolf_01",
        "filename": "gray_wolf_snow.jpg",
        "url": "https://images.unsplash.com/photo-1564865878688-9a244444042a",
        "subject": "gray wolf",
        "category": "animal",
        "attributes": ["gray fur", "pack predator", "winter", "timberland", "canis lupus"],
        "caption": "A majestic gray wolf howling in the snowy pine timberland.",
        "confidence": 0.95
    },
    {
        "id": "img_dog_01",
        "filename": "golden_retriever_park.jpg",
        "url": "https://images.unsplash.com/photo-1552053831-71594a27632d",
        "subject": "dog",
        "category": "animal",
        "attributes": ["golden retriever", "domestic pet", "grass", "playful"],
        "caption": "A happy golden retriever dog running outdoors in a park.",
        "confidence": 0.96
    },
    {
        "id": "img_quantum_01",
        "filename": "quantum_chip_processor.jpg",
        "url": "https://images.unsplash.com/photo-1635070041078-e363dbe005cb",
        "subject": "quantum computing",
        "category": "technology",
        "attributes": ["superconducting", "qubits", "silicon chip", "physics processor"],
        "caption": "A state-of-the-art superconducting quantum computing processor and qubit array.",
        "confidence": 0.92
    },
    {
        "id": "img_satellite_01",
        "filename": "space_satellite_orbit.jpg",
        "url": "https://images.unsplash.com/photo-1451187580459-43490279c0fa",
        "subject": "space satellite",
        "category": "technology",
        "attributes": ["orbital spacecraft", "earth orbit", "communications", "solar panels"],
        "caption": "An earth-observation space satellite orbiting the planet high above the atmosphere.",
        "confidence": 0.93
    },
    {
        "id": "img_ocean_01",
        "filename": "humpback_whale_ocean.jpg",
        "url": "https://images.unsplash.com/photo-1518709268805-4e9042af9f23",
        "subject": "ocean whale",
        "category": "nature",
        "attributes": ["marine life", "deep blue water", "breach"],
        "caption": "A giant humpback whale breaching out of the deep ocean water.",
        "confidence": 0.95
    },
    {
        "id": "img_mountain_01",
        "filename": "alpine_mountain_peak.jpg",
        "url": "https://images.unsplash.com/photo-1464822759023-fed622ff2c3b",
        "subject": "alpine mountain",
        "category": "nature",
        "attributes": ["snow peak", "sunrise", "landscape"],
        "caption": "Snow-capped alpine mountain peaks illuminated by the morning sunrise.",
        "confidence": 0.94
    },
    {
        "id": "img_blurry_01",
        "filename": "blurry_silhouette_fog.jpg",
        "url": "https://images.unsplash.com/photo-example-blurry",
        "subject": "unknown object",
        "category": "other",
        "attributes": ["foggy", "blurry", "shadow"],
        "caption": "A blurry, low-visibility shadow in dense fog.",
        "confidence": 0.45  # Low confidence -> Flagged
    }
]

BLOG_POSTS = [
    {
        "id": "p_fox_01",
        "title": "The Biology and Nocturnal Behavior of the Red Fox",
        "content": "The red fox (Vulpes vulpes) is the largest of the true foxes. Adapted to diverse habitats from wild woodlands and autumn forest canopies to suburban edges, their distinctive orange coat and bushy tail make them formidable survivors.",
        "target_subject": "red fox"
    },
    {
        "id": "p_wolf_01",
        "title": "Pack Hunting Tactics of the Gray Wolf in Winter",
        "content": "The gray wolf (Canis lupus) operates in disciplined packs. During harsh snowy winters, wolves coordinate across vast timberland territories to pursue prey with relentless endurance.",
        "target_subject": "gray wolf"
    },
    {
        "id": "p_dog_01",
        "title": "Essential Care Tips for Your Golden Retriever",
        "content": "Golden retrievers are one of the most beloved domestic pet dog breeds. Regular exercise in the park and active playtime maintain their physical agility and cheerful demeanor.",
        "target_subject": "dog"
    },
    {
        "id": "p_quantum_01",
        "title": "Advancements in Superconducting Qubits and Quantum Computing",
        "content": "Modern quantum processors leverage cryogenic superconducting circuits. By maintaining coherent qubits, researchers are tackling computational complexity far beyond classical silicon limits.",
        "target_subject": "quantum computing"
    },
    {
        "id": "p_satellite_01",
        "title": "Next-Generation Spacecraft and Satellite Communications",
        "content": "Low Earth orbit constellations rely on advanced satellites equipped with high-efficiency solar arrays and laser inter-satellite crosslinks to deliver low-latency global telecommunications.",
        "target_subject": "space satellite"
    },
    {
        "id": "p_cooking_01",
        "title": "Authentic Traditional Neapolitan Pizza Recipe",
        "content": "Making true Neapolitan pizza requires finely milled Type 00 flour, San Marzano tomatoes, fresh mozzarella di bufala, and a wood-fired oven reaching over 900 degrees Fahrenheit.",
        "target_subject": "culinary recipe"
    }
]


def seed_database():
    init_db()
    db = SessionLocal()
    try:
        # Ingest Images
        for item in IMAGE_CORPUS:
            img = db.query(ImageItem).filter(ImageItem.id == item["id"]).first()
            embedding = EmbeddingService.get_embedding(f"{item['subject']} {item['category']} {' '.join(item['attributes'])} {item['caption']}")
            status = "flagged_low_confidence" if item["confidence"] < 0.70 else "processed"

            if not img:
                img = ImageItem(
                    id=item["id"],
                    filename=item["filename"],
                    url=item["url"],
                    subject=item["subject"],
                    category=item["category"],
                    attributes=item["attributes"],
                    caption=item["caption"],
                    confidence=item["confidence"],
                    embedding=embedding,
                    status=status
                )
                db.add(img)

        # Ingest Blog Posts
        for p in BLOG_POSTS:
            post = db.query(BlogPost).filter(BlogPost.id == p["id"]).first()
            embedding = EmbeddingService.get_embedding(f"{p['title']} {p['content']} {p['target_subject']}")

            if not post:
                post = BlogPost(
                    id=p["id"],
                    title=p["title"],
                    content=p["content"],
                    target_subject=p["target_subject"],
                    embedding=embedding
                )
                db.add(post)

        # Ingest Cost Telemetry sample
        cost_entry = CostLog(
            operation="vision_batch_ingestion",
            model_id="google/gemini-2.0-flash-exp:free",
            input_tokens=1350,
            output_tokens=540,
            cost_micro_cents=525,
            duration_ms=4200
        )
        db.add(cost_entry)

        db.commit()
        logger.info(f"Database seeded with {len(IMAGE_CORPUS)} images and {len(BLOG_POSTS)} blog posts.")

    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
