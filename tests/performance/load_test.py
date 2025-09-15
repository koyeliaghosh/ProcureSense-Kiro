"""
Performance and Load Testing for ProcureSense

This module provides performance testing capabilities to validate
system behavior under various load conditions.
"""

import asyncio
import aiohttp
import time
import statistics
from typing import List, Dict, Any
from dataclasses import dataclass
import json


@dataclass
class LoadTestResult:
    """Results from a load test run."""
    total_requests: int
    successful_requests: int
    failed_requests: int
    average_response_time: float
    min_response_time: float
    max_response_time: float
    p95_response_time: float
    requests_per_second: float
    error_rate: float
    total_duration: float


class LoadTester:
    """Load testing utility for ProcureSense API."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def make_request(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Make a single HTTP request and measure response time."""
        start_time = time.time()
        
        try:
            async with self.session.post(
                f"{self.base_url}{endpoint}",
                json=data,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                response_time = time.time() - start_time
                response_data = await response.json()
                
                return {
                    "success": response.status == 200,
                    "status_code": response.status,
                    "response_time": response_time,
                    "response_data": response_data if response.status == 200 else None,
                    "error": None
                }
        
        except Exception as e:
            response_time = time.time() - start_time
            return {
                "success": False,
                "status_code": 0,
                "response_time": response_time,
                "response_data": None,
                "error": str(e)
            }
    
    async def run_load_test(
        self,
        endpoint: str,
        request_data_generator,
        concurrent_users: int = 10,
        requests_per_user: int = 10,
        ramp_up_time: float = 0
    ) -> LoadTestResult:
        """
        Run a load test with specified parameters.
        
        Args:
            endpoint: API endpoint to test
            request_data_generator: Function that generates request data
            concurrent_users: Number of concurrent users
            requests_per_user: Number of requests per user
            ramp_up_time: Time to ramp up all users (seconds)
        """
        
        async def user_session(user_id: int, delay: float):
            """Simulate a single user session."""
            if delay > 0:
                await asyncio.sleep(delay)
            
            results = []
            for i in range(requests_per_user):
                request_data = request_data_generator(user_id, i)
                result = await self.make_request(endpoint, request_data)
                results.append(result)
                
                # Small delay between requests from same user
                await asyncio.sleep(0.1)
            
            return results
        
        # Calculate ramp-up delay for each user
        ramp_delay = ramp_up_time / concurrent_users if concurrent_users > 1 else 0
        
        # Start load test
        start_time = time.time()
        
        # Create tasks for all users
        tasks = [
            user_session(user_id, user_id * ramp_delay)
            for user_id in range(concurrent_users)
        ]
        
        # Wait for all users to complete
        user_results = await asyncio.gather(*tasks)
        
        end_time = time.time()
        total_duration = end_time - start_time
        
        # Flatten results
        all_results = []
        for user_result in user_results:
            all_results.extend(user_result)
        
        # Calculate statistics
        successful_requests = sum(1 for r in all_results if r["success"])
        failed_requests = len(all_results) - successful_requests
        
        response_times = [r["response_time"] for r in all_results]
        
        return LoadTestResult(
            total_requests=len(all_results),
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            average_response_time=statistics.mean(response_times),
            min_response_time=min(response_times),
            max_response_time=max(response_times),
            p95_response_time=statistics.quantiles(response_times, n=20)[18] if len(response_times) > 1 else 0,
            requests_per_second=len(all_results) / total_duration,
            error_rate=(failed_requests / len(all_results)) * 100,
            total_duration=total_duration
        )


# Test Data Generators
def negotiation_request_generator(user_id: int, request_id: int) -> Dict[str, Any]:
    """Generate negotiation request data."""
    vendors = ["TechCorp", "SoftwareInc", "CloudVendor", "DataSystems", "AICompany"]
    categories = ["software", "hardware", "consulting", "cloud_services"]
    
    return {
        "vendor": f"{vendors[user_id % len(vendors)]}_{request_id}",
        "target_discount_pct": 10.0 + (request_id % 15),  # 10-24%
        "category": categories[user_id % len(categories)],
        "context": f"Load test request from user {user_id}, request {request_id}"
    }


def compliance_request_generator(user_id: int, request_id: int) -> Dict[str, Any]:
    """Generate compliance request data."""
    clauses = [
        "Standard terms and conditions apply with warranty coverage.",
        "Service level agreements include 99.9% uptime guarantee.",
        "Data protection and security measures are implemented.",
        "Payment terms are net 30 days from invoice date.",
        "Intellectual property rights are clearly defined."
    ]
    
    contract_types = ["software_license", "service_agreement", "consulting", "maintenance"]
    risk_levels = ["low", "medium", "high"]
    
    return {
        "clause": f"{clauses[request_id % len(clauses)]} (User {user_id}, Request {request_id})",
        "contract_type": contract_types[user_id % len(contract_types)],
        "risk_tolerance": risk_levels[request_id % len(risk_levels)]
    }


def forecast_request_generator(user_id: int, request_id: int) -> Dict[str, Any]:
    """Generate forecast request data."""
    categories = ["software", "hardware", "consulting", "cloud_services"]
    quarters = ["Q1 2024", "Q2 2024", "Q3 2024", "Q4 2024"]
    
    base_spend = 25000 + (user_id * 5000)
    planned_spend = base_spend + (request_id * 1000)
    
    return {
        "category": categories[user_id % len(categories)],
        "quarter": quarters[request_id % len(quarters)],
        "planned_spend": float(planned_spend),
        "current_budget": float(planned_spend * 1.2)  # 20% buffer
    }


# Test Scenarios
async def test_negotiation_load():
    """Test negotiation agent under load."""
    async with LoadTester() as tester:
        result = await tester.run_load_test(
            endpoint="/agent/negotiation",
            request_data_generator=negotiation_request_generator,
            concurrent_users=10,
            requests_per_user=5,
            ramp_up_time=2.0
        )
        
        print("=== Negotiation Agent Load Test ===")
        print(f"Total Requests: {result.total_requests}")
        print(f"Successful: {result.successful_requests}")
        print(f"Failed: {result.failed_requests}")
        print(f"Error Rate: {result.error_rate:.2f}%")
        print(f"Average Response Time: {result.average_response_time:.3f}s")
        print(f"95th Percentile: {result.p95_response_time:.3f}s")
        print(f"Requests/Second: {result.requests_per_second:.2f}")
        print()
        
        return result


async def test_compliance_load():
    """Test compliance agent under load."""
    async with LoadTester() as tester:
        result = await tester.run_load_test(
            endpoint="/agent/compliance",
            request_data_generator=compliance_request_generator,
            concurrent_users=8,
            requests_per_user=5,
            ramp_up_time=1.5
        )
        
        print("=== Compliance Agent Load Test ===")
        print(f"Total Requests: {result.total_requests}")
        print(f"Successful: {result.successful_requests}")
        print(f"Failed: {result.failed_requests}")
        print(f"Error Rate: {result.error_rate:.2f}%")
        print(f"Average Response Time: {result.average_response_time:.3f}s")
        print(f"95th Percentile: {result.p95_response_time:.3f}s")
        print(f"Requests/Second: {result.requests_per_second:.2f}")
        print()
        
        return result


async def test_forecast_load():
    """Test forecast agent under load."""
    async with LoadTester() as tester:
        result = await tester.run_load_test(
            endpoint="/agent/forecast",
            request_data_generator=forecast_request_generator,
            concurrent_users=6,
            requests_per_user=5,
            ramp_up_time=1.0
        )
        
        print("=== Forecast Agent Load Test ===")
        print(f"Total Requests: {result.total_requests}")
        print(f"Successful: {result.successful_requests}")
        print(f"Failed: {result.failed_requests}")
        print(f"Error Rate: {result.error_rate:.2f}%")
        print(f"Average Response Time: {result.average_response_time:.3f}s")
        print(f"95th Percentile: {result.p95_response_time:.3f}s")
        print(f"Requests/Second: {result.requests_per_second:.2f}")
        print()
        
        return result


async def test_mixed_load():
    """Test mixed workload across all agents."""
    async with LoadTester() as tester:
        # Run all agents concurrently
        tasks = [
            tester.run_load_test(
                "/agent/negotiation",
                negotiation_request_generator,
                concurrent_users=5,
                requests_per_user=3
            ),
            tester.run_load_test(
                "/agent/compliance",
                compliance_request_generator,
                concurrent_users=5,
                requests_per_user=3
            ),
            tester.run_load_test(
                "/agent/forecast",
                forecast_request_generator,
                concurrent_users=5,
                requests_per_user=3
            )
        ]
        
        results = await asyncio.gather(*tasks)
        
        print("=== Mixed Load Test Results ===")
        agent_names = ["Negotiation", "Compliance", "Forecast"]
        
        total_requests = sum(r.total_requests for r in results)
        total_successful = sum(r.successful_requests for r in results)
        total_failed = sum(r.failed_requests for r in results)
        
        print(f"Overall Total Requests: {total_requests}")
        print(f"Overall Successful: {total_successful}")
        print(f"Overall Failed: {total_failed}")
        print(f"Overall Error Rate: {(total_failed/total_requests)*100:.2f}%")
        print()
        
        for i, (name, result) in enumerate(zip(agent_names, results)):
            print(f"{name} Agent:")
            print(f"  Requests: {result.total_requests}")
            print(f"  Success Rate: {(result.successful_requests/result.total_requests)*100:.1f}%")
            print(f"  Avg Response Time: {result.average_response_time:.3f}s")
            print(f"  RPS: {result.requests_per_second:.2f}")
        
        return results


async def main():
    """Run all load tests."""
    print("Starting ProcureSense Load Tests...")
    print("=" * 50)
    
    try:
        # Individual agent tests
        await test_negotiation_load()
        await test_compliance_load()
        await test_forecast_load()
        
        # Mixed load test
        await test_mixed_load()
        
        print("Load testing completed successfully!")
        
    except Exception as e:
        print(f"Load testing failed: {e}")


if __name__ == "__main__":
    asyncio.run(main())