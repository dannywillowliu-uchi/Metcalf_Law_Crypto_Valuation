"""
Dune Query Manager

Handles creating and executing Dune Analytics queries via API.
"""

import requests
import time
import os
from typing import Optional, Dict, Any
from pathlib import Path
import json
import io

class DuneQueryManager:
    """
    Manages Dune Analytics queries: create, execute, and fetch results.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Dune Query Manager.
        
        Parameters
        ----------
        api_key : str, optional
            Dune Analytics API key (default: from DUNE_API_KEY env var)
        """
        self.api_key = api_key or os.getenv("DUNE_API_KEY")
        if not self.api_key:
            raise ValueError("Dune API key required. Set DUNE_API_KEY environment variable.")
        
        self.base_url = "https://api.dune.com/api/v1"
        self.headers = {
            "X-DUNE-API-Key": self.api_key,
            "Content-Type": "application/json"
        }
    
    def create_query(
        self,
        name: str,
        sql: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict]:
        """
        Create a new Dune query.
        
        Parameters
        ----------
        name : str
            Query name
        sql : str
            SQL query string
        parameters : dict, optional
            Query parameters
        
        Returns
        -------
        dict
            Query creation response with query_id
        """
        url = f"{self.base_url}/query"
        
        payload = {
            "name": name,
            "query_sql": sql
        }
        
        if parameters:
            payload["parameters"] = parameters
        
        print(f"Creating Dune query: {name}")
        print(f"SQL length: {len(sql)} characters")
        
        try:
            response = requests.post(url, headers=self.headers, json=payload, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                query_id = result.get("query_id")
                print(f"✅ Query created successfully: Query #{query_id}")
                return result
            else:
                print(f"❌ Error creating query: {response.status_code}")
                print(f"   Response: {response.text[:200]}")
                return None
                
        except Exception as e:
            print(f"❌ Exception creating query: {e}")
            return None
    
    def execute_query(
        self,
        query_id: int,
        parameters: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict]:
        """
        Execute a Dune query.
        
        Parameters
        ----------
        query_id : int
            Dune query ID
        parameters : dict, optional
            Query parameters
        
        Returns
        -------
        dict
            Execution response with execution_id
        """
        url = f"{self.base_url}/query/{query_id}/execute"
        
        payload = {}
        if parameters:
            payload["parameters"] = parameters
        
        print(f"Executing Dune query #{query_id}...")
        print(f"⚠️  This will cost ~300 credits!")
        
        try:
            response = requests.post(url, headers=self.headers, json=payload, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                execution_id = result.get("execution_id")
                print(f"✅ Query execution started: Execution #{execution_id}")
                return result
            else:
                print(f"❌ Error executing query: {response.status_code}")
                print(f"   Response: {response.text[:200]}")
                return None
                
        except Exception as e:
            print(f"❌ Exception executing query: {e}")
            return None
    
    def get_execution_status(
        self,
        execution_id: str
    ) -> Optional[Dict]:
        """
        Get execution status.
        
        Parameters
        ----------
        execution_id : str
            Execution ID
        
        Returns
        -------
        dict
            Execution status
        """
        url = f"{self.base_url}/execution/{execution_id}/status"
        
        try:
            response = requests.get(url, headers=self.headers, timeout=30)
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"❌ Error getting status: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Exception getting status: {e}")
            return None
    
    def wait_for_execution(
        self,
        execution_id: str,
        max_wait: int = 300,
        check_interval: int = 5
    ) -> bool:
        """
        Wait for query execution to complete.
        
        Parameters
        ----------
        execution_id : str
            Execution ID
        max_wait : int
            Maximum wait time in seconds (default: 300)
        check_interval : int
            Check interval in seconds (default: 5)
        
        Returns
        -------
        bool
            True if execution completed successfully
        """
        start_time = time.time()
        
        print(f"Waiting for execution #{execution_id} to complete...")
        
        while time.time() - start_time < max_wait:
            status = self.get_execution_status(execution_id)
            
            if status:
                state = status.get("state")
                print(f"   Status: {state}")
                
                if state == "QUERY_STATE_COMPLETED":
                    print(f"✅ Execution completed successfully")
                    return True
                elif state == "QUERY_STATE_FAILED":
                    print(f"❌ Execution failed")
                    return False
            
            time.sleep(check_interval)
        
        print(f"⏱️  Timeout waiting for execution")
        return False
    
    def get_query_results_csv(
        self,
        query_id: int
    ) -> Optional[str]:
        """
        Get query results as CSV (no execution cost).
        
        Parameters
        ----------
        query_id : int
            Dune query ID
        
        Returns
        -------
        str
            CSV content as string
        """
        url = f"{self.base_url}/query/{query_id}/results/csv"
        
        try:
            response = requests.get(url, headers=self.headers, timeout=30)
            
            if response.status_code == 200:
                return response.text
            elif response.status_code == 404:
                print(f"⚠️  Query results not found. Query may need to be executed first.")
                return None
            else:
                print(f"❌ Error fetching CSV: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Exception fetching CSV: {e}")
            return None

