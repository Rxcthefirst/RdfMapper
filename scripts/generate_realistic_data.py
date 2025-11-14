#!/usr/bin/env python3
"""Generate realistic test data for streaming performance benchmarks."""

import csv
import json
import random
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict


class RealisticDataGenerator:
    """Generate realistic business data for testing."""

    def __init__(self):
        self.departments = [
            'Engineering', 'Sales', 'Marketing', 'HR', 'Finance',
            'Operations', 'Customer Success', 'Product', 'Legal', 'IT'
        ]

        self.cities = [
            'New York', 'San Francisco', 'Chicago', 'Austin', 'Seattle',
            'Boston', 'Los Angeles', 'Denver', 'Atlanta', 'Miami'
        ]

        self.states = [
            'NY', 'CA', 'IL', 'TX', 'WA', 'MA', 'CO', 'GA', 'FL'
        ]

        self.first_names = [
            'James', 'Mary', 'John', 'Patricia', 'Robert', 'Jennifer', 'Michael', 'Linda',
            'William', 'Elizabeth', 'David', 'Barbara', 'Richard', 'Susan', 'Joseph', 'Jessica',
            'Thomas', 'Sarah', 'Christopher', 'Karen', 'Charles', 'Nancy', 'Daniel', 'Lisa',
            'Matthew', 'Betty', 'Anthony', 'Helen', 'Mark', 'Sandra', 'Donald', 'Donna'
        ]

        self.last_names = [
            'Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis',
            'Rodriguez', 'Martinez', 'Hernandez', 'Lopez', 'Gonzalez', 'Wilson', 'Anderson',
            'Thomas', 'Taylor', 'Moore', 'Jackson', 'Martin', 'Lee', 'Perez', 'Thompson',
            'White', 'Harris', 'Sanchez', 'Clark', 'Ramirez', 'Lewis', 'Robinson', 'Walker'
        ]

        self.skills = [
            'Python', 'Java', 'JavaScript', 'SQL', 'React', 'Node.js', 'AWS', 'Docker',
            'Kubernetes', 'Machine Learning', 'Data Analysis', 'Project Management',
            'Agile', 'Scrum', 'Leadership', 'Communication', 'Problem Solving'
        ]

        self.project_types = [
            'Web Development', 'Mobile App', 'Data Pipeline', 'ML Model', 'API Integration',
            'Infrastructure', 'Security Audit', 'Database Migration', 'UI/UX Redesign'
        ]

    def generate_employee_data(self, num_rows: int) -> List[Dict]:
        """Generate realistic employee data."""
        employees = []
        base_date = datetime(2020, 1, 1)

        for i in range(num_rows):
            first_name = random.choice(self.first_names)
            last_name = random.choice(self.last_names)
            department = random.choice(self.departments)

            # Generate realistic salary based on department and experience
            base_salary = {
                'Engineering': 95000, 'Sales': 75000, 'Marketing': 70000,
                'HR': 65000, 'Finance': 80000, 'Operations': 70000,
                'Customer Success': 65000, 'Product': 90000, 'Legal': 120000, 'IT': 85000
            }.get(department, 70000)

            experience_years = random.randint(0, 20)
            salary = base_salary + (experience_years * random.randint(2000, 5000)) + random.randint(-10000, 15000)

            # Generate hire date
            hire_date = base_date + timedelta(days=random.randint(0, 1800))

            # Generate realistic email
            email_first = first_name.lower()
            email_last = last_name.lower()
            email = f"{email_first}.{email_last}@company.com"
            if random.random() < 0.1:  # 10% chance of number suffix
                email = f"{email_first}.{email_last}{random.randint(1, 99)}@company.com"

            employee = {
                'EmployeeID': f'EMP{i+1000:06d}',
                'FirstName': first_name,
                'LastName': last_name,
                'FullName': f'{first_name} {last_name}',
                'Email': email,
                'Department': department,
                'JobTitle': self._generate_job_title(department, experience_years),
                'Salary': salary,
                'HireDate': hire_date.strftime('%Y-%m-%d'),
                'Age': random.randint(22, 65),
                'City': random.choice(self.cities),
                'State': random.choice(self.states),
                'ManagerID': f'EMP{random.randint(1000, 1000 + max(0, i-10)):06d}' if i > 10 else '',
                'IsActive': random.choice(['true', 'false']) if random.random() < 0.05 else 'true',
                'Skills': ', '.join(random.sample(self.skills, random.randint(2, 6))),
                'YearsExperience': experience_years,
                'PerformanceRating': round(random.uniform(2.5, 5.0), 1),
                'LastReviewDate': (hire_date + timedelta(days=random.randint(365, 1500))).strftime('%Y-%m-%d'),
                'Notes': f'Employee notes for {first_name} {last_name}. Performance: {"Excellent" if salary > base_salary + 20000 else "Good"}.'
            }

            employees.append(employee)

        return employees

    def _generate_job_title(self, department: str, experience: int) -> str:
        """Generate realistic job title based on department and experience."""
        titles = {
            'Engineering': ['Software Engineer', 'Senior Software Engineer', 'Staff Engineer', 'Principal Engineer', 'Engineering Manager'],
            'Sales': ['Sales Representative', 'Account Executive', 'Senior Account Executive', 'Sales Manager', 'VP Sales'],
            'Marketing': ['Marketing Specialist', 'Marketing Manager', 'Senior Marketing Manager', 'Marketing Director', 'VP Marketing'],
            'HR': ['HR Specialist', 'HR Manager', 'Senior HR Manager', 'HR Director', 'VP Human Resources'],
            'Finance': ['Financial Analyst', 'Senior Financial Analyst', 'Finance Manager', 'Finance Director', 'CFO'],
            'Operations': ['Operations Specialist', 'Operations Manager', 'Senior Operations Manager', 'Operations Director', 'COO'],
            'Customer Success': ['Customer Success Specialist', 'Customer Success Manager', 'Senior CSM', 'CS Director', 'VP Customer Success'],
            'Product': ['Product Analyst', 'Product Manager', 'Senior Product Manager', 'Product Director', 'VP Product'],
            'Legal': ['Legal Specialist', 'Legal Counsel', 'Senior Legal Counsel', 'Legal Director', 'General Counsel'],
            'IT': ['IT Specialist', 'IT Manager', 'Senior IT Manager', 'IT Director', 'CTO']
        }

        dept_titles = titles.get(department, ['Specialist', 'Manager', 'Senior Manager', 'Director', 'VP'])

        if experience < 2:
            return dept_titles[0]
        elif experience < 5:
            return dept_titles[1] if len(dept_titles) > 1 else dept_titles[0]
        elif experience < 10:
            return dept_titles[2] if len(dept_titles) > 2 else dept_titles[1]
        elif experience < 15:
            return dept_titles[3] if len(dept_titles) > 3 else dept_titles[2]
        else:
            return dept_titles[4] if len(dept_titles) > 4 else dept_titles[3]

    def generate_project_data(self, num_rows: int, employee_count: int) -> List[Dict]:
        """Generate realistic project data."""
        projects = []
        base_date = datetime(2020, 1, 1)

        for i in range(num_rows):
            start_date = base_date + timedelta(days=random.randint(0, 1500))
            duration_days = random.randint(30, 365)
            end_date = start_date + timedelta(days=duration_days)

            project = {
                'ProjectID': f'PROJ{i+1:06d}',
                'ProjectName': f'{random.choice(self.project_types)} - Phase {random.randint(1, 3)}',
                'Description': f'Strategic {random.choice(self.project_types).lower()} initiative for Q{random.randint(1, 4)} delivery.',
                'StartDate': start_date.strftime('%Y-%m-%d'),
                'EndDate': end_date.strftime('%Y-%m-%d'),
                'Budget': random.randint(50000, 2000000),
                'Status': random.choice(['Planning', 'In Progress', 'On Hold', 'Completed', 'Cancelled']),
                'Priority': random.choice(['Low', 'Medium', 'High', 'Critical']),
                'ProjectManagerID': f'EMP{random.randint(1000, 1000 + min(employee_count, 100)):06d}',
                'DepartmentOwner': random.choice(self.departments),
                'EstimatedHours': random.randint(500, 5000),
                'ActualHours': random.randint(400, 6000),
                'CompletionPercentage': random.randint(0, 100),
                'RiskLevel': random.choice(['Low', 'Medium', 'High']),
                'ClientID': f'CLIENT{random.randint(1, 50):03d}' if random.random() < 0.7 else '',
                'Notes': f'Project tracking notes and status updates. Last updated {(start_date + timedelta(days=random.randint(1, duration_days))).strftime("%Y-%m-%d")}.'
            }

            projects.append(project)

        return projects

    def write_csv(self, data: List[Dict], filepath: Path) -> None:
        """Write data to CSV file."""
        if not data:
            return

        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)

    def generate_test_datasets(self, base_path: Path, sizes: List[int]) -> Dict[str, List[Path]]:
        """Generate multiple test datasets of different sizes."""
        generated_files = {'employees': [], 'projects': []}

        base_path.mkdir(exist_ok=True)

        for size in sizes:
            print(f"Generating {size:,} employee records...")
            employees = self.generate_employee_data(size)
            emp_file = base_path / f'employees_{size}.csv'
            self.write_csv(employees, emp_file)
            generated_files['employees'].append(emp_file)

            # Generate proportional number of projects (roughly 1 project per 10 employees)
            project_count = max(10, size // 10)
            print(f"Generating {project_count:,} project records...")
            projects = self.generate_project_data(project_count, size)
            proj_file = base_path / f'projects_{size}.csv'
            self.write_csv(projects, proj_file)
            generated_files['projects'].append(proj_file)

        return generated_files


if __name__ == "__main__":
    generator = RealisticDataGenerator()
    test_data_path = Path("test_data")

    # Generate datasets of different sizes
    sizes = [10_000, 100_000, 500_000, 1_000_000]

    print("🏭 Generating Realistic Test Data")
    print("=" * 40)

    files = generator.generate_test_datasets(test_data_path, sizes)

    print(f"\n✅ Generated test datasets:")
    for dataset_type, file_list in files.items():
        print(f"  {dataset_type.title()}:")
        for file_path in file_list:
            size_mb = file_path.stat().st_size / (1024 * 1024)
            print(f"    📁 {file_path.name} ({size_mb:.1f} MB)")

    print(f"\n💡 Files saved to: {test_data_path.absolute()}")
    print(f"Use these files with realistic_streaming_test.py for benchmarking.")
