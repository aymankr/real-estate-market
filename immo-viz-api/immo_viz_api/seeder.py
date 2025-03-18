from pathlib import Path
from sqlalchemy.orm import Session
from immo_viz_api.database import get_viz_db
from immo_viz_api.models import Region, Department, City

REGIONS_FILE_PATH: Path = Path("./immo_viz_api/resources/france_regions.csv")
DEPARTMENTS_FILE_PATH: Path = Path("./immo_viz_api/resources/france_departments.csv")
CITIES_FILE_PATH: Path = Path("./immo_viz_api/resources/france_cities.csv")


def seed_regions(db: Session):
    """Seed regions from the CSV file."""

    inserted_regions_count: int = 0
    print("Seeding regions...")
    with REGIONS_FILE_PATH.open("r") as file:
        file.readline()
        for line in file:
            insee_code, name, area, population, capital_city_insee_code = (
                line.strip().split(",")
            )
            region = Region(
                insee_code=int(insee_code),
                name=name,
                area=float(area),
                population=int(population),
                capital_city_insee_code=str(capital_city_insee_code),
            )
            db.add(region)
            inserted_regions_count += 1
    db.commit()
    print(f"{inserted_regions_count} regions seeded successfully.")


def seed_departments(db: Session):
    """Seed departments from the CSV file."""

    inserted_departments_count: int = 0
    print("Seeding departments...")
    with DEPARTMENTS_FILE_PATH.open("r") as file:
        file.readline()
        for line in file:
            (
                insee_code,
                name,
                area,
                population,
                capital_city_insee_code,
                region_insee_code,
            ) = line.strip().split(",")
            department = Department(
                insee_code=int(insee_code),
                name=name,
                area=float(area),
                population=int(population),
                capital_city_insee_code=str(capital_city_insee_code),
                region_insee_code=str(region_insee_code),
            )
            db.add(department)
            inserted_departments_count += 1
    db.commit()
    print(f"{inserted_departments_count} departments seeded successfully.")


def seed_cities(db: Session):
    """Seed cities from the CSV file."""

    inserted_cities_count: int = 0
    print("Seeding cities...")
    with CITIES_FILE_PATH.open("r") as file:
        file.readline()
        for line in file:
            insee_code, zip_code, name, latitude, longitude, department_insee_code = (
                line.strip().split(",")
            )
            city = City(
                insee_code=str(insee_code),
                name=name,
                zip_code=int(zip_code),
                latitude=float(latitude) if len(latitude) > 0 else None,
                longitude=float(longitude) if len(longitude) > 0 else None,
                department_insee_code=str(department_insee_code),
            )
            db.add(city)
            inserted_cities_count += 1
    db.commit()
    print(f"{inserted_cities_count} cities seeded successfully.")


if __name__ == "__main__":
    db_session = next(get_viz_db())  # Get a session
    seed_regions(db_session)
    seed_departments(db_session)
    seed_cities(db_session)
    db_session.close()
