"""
Tests for the High School Management System API
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app

client = TestClient(app)


class TestRootEndpoint:
    """Test the root endpoint"""
    
    def test_root_redirects_to_static(self):
        """Test that root endpoint redirects to static index"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestGetActivities:
    """Test the get activities endpoint"""
    
    def test_get_activities_returns_all_activities(self):
        """Test that get activities returns all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert len(data) > 0
    
    def test_get_activities_contains_expected_activities(self):
        """Test that response contains expected activities"""
        response = client.get("/activities")
        data = response.json()
        expected_activities = [
            "Baseball Club",
            "Soccer Team",
            "Art Club",
            "Drama Club",
            "Debate Team",
            "Robotics Club",
            "Chess Club",
            "Programming Class",
            "Gym Class"
        ]
        for activity in expected_activities:
            assert activity in data
    
    def test_activity_has_required_fields(self):
        """Test that each activity has required fields"""
        response = client.get("/activities")
        data = response.json()
        for activity_name, activity_data in data.items():
            assert "description" in activity_data
            assert "schedule" in activity_data
            assert "max_participants" in activity_data
            assert "participants" in activity_data
            assert isinstance(activity_data["participants"], list)


class TestSignupForActivity:
    """Test the signup endpoint"""
    
    def test_signup_for_valid_activity(self):
        """Test signing up for a valid activity"""
        response = client.post(
            "/activities/Baseball%20Club/signup",
            params={"email": "newstudent@mergington.edu"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "newstudent@mergington.edu" in data["message"]
    
    def test_signup_for_nonexistent_activity(self):
        """Test signing up for a nonexistent activity"""
        response = client.post(
            "/activities/NonExistent%20Club/signup",
            params={"email": "test@mergington.edu"}
        )
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]
    
    def test_signup_already_registered(self):
        """Test signing up when already registered"""
        # Try to signup with an already registered email
        response = client.post(
            "/activities/Baseball%20Club/signup",
            params={"email": "alex@mergington.edu"}
        )
        assert response.status_code == 400
        data = response.json()
        assert "already signed up" in data["detail"]
    
    def test_signup_returns_confirmation_message(self):
        """Test that signup returns a confirmation message"""
        response = client.post(
            "/activities/Chess%20Club/signup",
            params={"email": "testsignup@mergington.edu"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "Signed up" in data["message"]


class TestUnregisterFromActivity:
    """Test the unregister endpoint"""
    
    def test_unregister_from_valid_activity(self):
        """Test unregistering from a valid activity"""
        # First signup
        client.post(
            "/activities/Drama%20Club/signup",
            params={"email": "unreg_test@mergington.edu"}
        )
        # Then unregister
        response = client.delete(
            "/activities/Drama%20Club/unregister",
            params={"email": "unreg_test@mergington.edu"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "Unregistered" in data["message"]
    
    def test_unregister_from_nonexistent_activity(self):
        """Test unregistering from a nonexistent activity"""
        response = client.delete(
            "/activities/Fake%20Club/unregister",
            params={"email": "test@mergington.edu"}
        )
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]
    
    def test_unregister_when_not_registered(self):
        """Test unregistering when not currently registered"""
        response = client.delete(
            "/activities/Art%20Club/unregister",
            params={"email": "notregistered@mergington.edu"}
        )
        assert response.status_code == 400
        data = response.json()
        assert "not registered" in data["detail"]
    
    def test_unregister_returns_confirmation_message(self):
        """Test that unregister returns a confirmation message"""
        # First signup
        client.post(
            "/activities/Robotics%20Club/signup",
            params={"email": "unreg_test2@mergington.edu"}
        )
        # Then unregister
        response = client.delete(
            "/activities/Robotics%20Club/unregister",
            params={"email": "unreg_test2@mergington.edu"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "unreg_test2@mergington.edu" in data["message"]


class TestActivityParticipationLimits:
    """Test activity participant limits"""
    
    def test_activity_max_participants_exists(self):
        """Test that activities have max_participants field"""
        response = client.get("/activities")
        data = response.json()
        for activity in data.values():
            assert "max_participants" in activity
            assert isinstance(activity["max_participants"], int)
            assert activity["max_participants"] > 0
    
    def test_participant_count_consistency(self):
        """Test that participant count doesn't exceed max"""
        response = client.get("/activities")
        data = response.json()
        for activity in data.values():
            assert len(activity["participants"]) <= activity["max_participants"]


class TestIntegrationScenarios:
    """Test integration scenarios"""
    
    def test_signup_and_unregister_flow(self):
        """Test complete signup and unregister flow"""
        email = "integration_test@mergington.edu"
        activity = "Debate%20Team"
        
        # Get initial count
        response = client.get("/activities")
        initial_count = len(response.json()["Debate Team"]["participants"])
        
        # Signup
        signup_response = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        assert signup_response.status_code == 200
        
        # Verify signup
        response = client.get("/activities")
        new_count = len(response.json()["Debate Team"]["participants"])
        assert new_count == initial_count + 1
        
        # Unregister
        unregister_response = client.delete(
            f"/activities/{activity}/unregister",
            params={"email": email}
        )
        assert unregister_response.status_code == 200
        
        # Verify unregister
        response = client.get("/activities")
        final_count = len(response.json()["Debate Team"]["participants"])
        assert final_count == initial_count
