import os
import sys
import asyncio
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

# Ensure project root is in path
sys.path.append(os.path.dirname(__file__))

from main import app
from database import engine, Base, AsyncSessionLocal
import models

async def reset_db():
    """Drops and rebuilds all database schemas for clean, isolated validation."""
    print("Resetting database...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    print("Database reset completed successfully!")

async def run_tests():
    """Runs a complete test suite of 20 distinct scenarios testing REST endpoints and security."""
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        
        print("\n--- Test Case 1: Register Seeker ---")
        seeker_data = {
            "username": "seeker1",
            "email": "seeker1@test.com",
            "password": "password123",
            "role": "seeker"
        }
        response = await client.post("/api/v1/auth/register", json=seeker_data)
        print("Status:", response.status_code)
        print("Response:", response.json())
        assert response.status_code == 201
        assert response.json()["username"] == "seeker1"
        assert response.json()["role"] == "seeker"

        print("\n--- Test Case 2: Register Employer ---")
        employer_data = {
            "username": "employer1",
            "email": "employer1@test.com",
            "password": "password123",
            "role": "employer"
        }
        response = await client.post("/api/v1/auth/register", json=employer_data)
        print("Status:", response.status_code)
        print("Response:", response.json())
        assert response.status_code == 201
        assert response.json()["username"] == "employer1"
        assert response.json()["role"] == "employer"

        print("\n--- Test Case 3: Register Admin ---")
        admin_data = {
            "username": "admin1",
            "email": "admin1@test.com",
            "password": "password123",
            "role": "admin"
        }
        response = await client.post("/api/v1/auth/register", json=admin_data)
        print("Status:", response.status_code)
        assert response.status_code == 201

        print("\n--- Test Case 4: Login Seeker ---")
        login_data = {
            "username": "seeker1",
            "password": "password123"
        }
        response = await client.post("/api/v1/auth/login", data=login_data)
        print("Status:", response.status_code)
        print("Response:", response.json())
        assert response.status_code == 200
        seeker_token = response.json()["access_token"]
        seeker_headers = {"Authorization": f"Bearer {seeker_token}"}

        print("\n--- Test Case 5: Login Employer ---")
        login_data = {
            "username": "employer1",
            "password": "password123"
        }
        response = await client.post("/api/v1/auth/login", data=login_data)
        print("Status:", response.status_code)
        print("Response:", response.json())
        assert response.status_code == 200
        employer_token = response.json()["access_token"]
        employer_headers = {"Authorization": f"Bearer {employer_token}"}

        print("\n--- Test Case 6: Login Admin ---")
        login_data = {
            "username": "admin1",
            "password": "password123"
        }
        response = await client.post("/api/v1/auth/login", data=login_data)
        assert response.status_code == 200
        admin_token = response.json()["access_token"]
        admin_headers = {"Authorization": f"Bearer {admin_token}"}

        print("\n--- Test Case 7: Create Job Opportunity (Employer) ---")
        job_data = {
            "title": "Junior Python Developer",
            "description": "We are seeking a high-potential junior python developer to join our team.",
            "requirements": "Basic Python knowledge, FastAPI exposure, relational database basics.",
            "location": "Freetown, Sierra Leone",
            "job_type": "Full-time",
            "salary_range": "SLL 5,000,000 - 8,000,000"
        }
        response = await client.post("/api/v1/jobs", json=job_data, headers=employer_headers)
        print("Status:", response.status_code)
        print("Response:", response.json())
        assert response.status_code == 201
        job_id = response.json()["id"]

        print("\n--- Test Case 8: Create Job Opportunity (Seeker - Should Fail) ---")
        response = await client.post("/api/v1/jobs", json=job_data, headers=seeker_headers)
        print("Status (Expected 403):", response.status_code)
        assert response.status_code == 403

        print("\n--- Test Case 9: View Job Listings (Public) ---")
        response = await client.get("/api/v1/jobs")
        print("Status:", response.status_code)
        print("listings count:", len(response.json()))
        assert response.status_code == 200
        assert len(response.json()) >= 1

        print("\n--- Test Case 10: View Job Listings with Keyword Filter ---")
        response = await client.get("/api/v1/jobs?keyword=python")
        print("Status:", response.status_code)
        assert response.status_code == 200
        assert len(response.json()) >= 1

        print("\n--- Test Case 11: Seeker Updates Seeker Profile ---")
        profile_data = {
            "full_name": "Julius Maada Seeker",
            "bio": "Enthusiastic S4 Limkokwing Creative Technology Student.",
            "skills": "Python, JavaScript, SQL, HTML",
            "education": "Diploma in Information Technology"
        }
        response = await client.put("/api/v1/auth/profile", json=profile_data, headers=seeker_headers)
        print("Status:", response.status_code)
        print("Response:", response.json())
        assert response.status_code == 200
        assert response.json()["full_name"] == "Julius Maada Seeker"

        print("\n--- Test Case 12: Seeker Applies for Job ---")
        # Prepare a dummy PDF file content
        dummy_pdf = b"%PDF-1.4 Mock PDF Content"
        files = {
            "file": ("my_resume.pdf", dummy_pdf, "application/pdf")
        }
        data = {
            "cover_letter": "I would love to apply for this wonderful opportunity!"
        }
        response = await client.post(f"/api/v1/jobs/{job_id}/apply", data=data, files=files, headers=seeker_headers)
        print("Status:", response.status_code)
        print("Response:", response.json())
        assert response.status_code == 201
        application_id = response.json()["id"]

        print("\n--- Test Case 13: Seeker Applies with Large File (Should Fail) ---")
        large_pdf = b"%PDF-1.4" + b"X" * (6 * 1024 * 1024)  # 6MB
        files_large = {
            "file": ("large_resume.pdf", large_pdf, "application/pdf")
        }
        response = await client.post(f"/api/v1/jobs/{job_id}/apply", data=data, files=files_large, headers=seeker_headers)
        print("Status (Expected 400):", response.status_code)
        assert response.status_code == 400

        print("\n--- Test Case 14: Seeker Applies with Non-PDF File (Should Fail) ---")
        files_text = {
            "file": ("resume.txt", b"Some plain text resume", "text/plain")
        }
        response = await client.post(f"/api/v1/jobs/{job_id}/apply", data=data, files=files_text, headers=seeker_headers)
        print("Status (Expected 400):", response.status_code)
        assert response.status_code == 400

        print("\n--- Test Case 15: Seeker Views Their Applications ---")
        response = await client.get("/api/v1/applications", headers=seeker_headers)
        print("Status:", response.status_code)
        print("Response:", response.json())
        assert response.status_code == 200
        assert len(response.json()) == 1

        print("\n--- Test Case 16: Employer Views Applications ---")
        response = await client.get("/api/v1/applications", headers=employer_headers)
        print("Status:", response.status_code)
        print("Response:", response.json())
        assert response.status_code == 200
        assert len(response.json()) == 1

        print("\n--- Test Case 17: Employer Updates Application Status ---")
        status_data = {
            "status": "interviewing"
        }
        response = await client.patch(f"/api/v1/applications/{application_id}", json=status_data, headers=employer_headers)
        print("Status:", response.status_code)
        print("Response:", response.json())
        assert response.status_code == 200
        assert response.json()["status"] == "interviewing"

        print("\n--- Test Case 18: Seeker Views Applications and Confirms Status Update ---")
        response = await client.get("/api/v1/applications", headers=seeker_headers)
        print("Status:", response.status_code)
        print("Status value:", response.json()[0]["status"])
        assert response.status_code == 200
        assert response.json()[0]["status"] == "interviewing"

        print("\n--- Test Case 19: Employer Deletes/Closes Job Listing ---")
        response = await client.delete(f"/api/v1/jobs/{job_id}", headers=employer_headers)
        print("Status (Expected 204):", response.status_code)
        assert response.status_code == 204

        print("\n--- Test Case 20: View Deleted Job Listing (Expected 404) ---")
        response = await client.get(f"/api/v1/jobs/{job_id}")
        print("Status (Expected 404):", response.status_code)
        assert response.status_code == 404

        print("==================================================")
        print("=== ALL 20 API TEST CASES COMPLETED SUCCESSFULLY! ===")
        print("==================================================")

async def main():
    await reset_db()
    await run_tests()

if __name__ == "__main__":
    asyncio.run(main())
