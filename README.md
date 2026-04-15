## Features

- **Student Management**: Create, read, update, and delete student records
- **Course Management**: Manage course information and associate students with courses
- **Authentication**: JWT-based authentication for secure API access
- **RESTful API**: Well-structured endpoints following REST principles
- **Data Validation**: Comprehensive serializers for data integrity

## Installation

### Prerequisites

- Python 3.12 or higher
- uv

### Setup

1. Clone the repository:

   ```bash
   git clone <repository-url>
   cd recover-folder-structure
   ```

2. Create a virtual environment:

   ```bash
   uv venv .venv
   source .venv/bin/activate
   ```

3. Install dependencies from pyproject.toml:

   ```bash
   uv sync
   ```

4. Run database migrations:

   ```bash
   python manage.py migrate
   ```

5. Create a superuser (optional, for admin access):
   ```bash
   python manage.py createsuperuser
   ```

## Running the Application

Start the development server:

```bash
python manage.py runserver
```

The API will be available at `http://127.0.0.1:8000/`

## API Documentation

### Authentication

The API uses JWT (JSON Web Tokens) for authentication. To access protected endpoints, you need to obtain a token first.

#### Obtain Token

```
POST /api/token/
Content-Type: application/json

{
  "username": "your_username",
  "password": "your_password"
}
```

Response:

```json
{
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoicmVmcmVzaCIsImV4cCI6MTc3NTgwOTYxMywiaWF0IjoxNzc1NzIzMjEzLCJqdGkiOiIxNjZhMDAwYzdjYTg0ZGY3YmExZDFhM2Q1MGFkZDQ3MCIsInVzZXJfaWQiOiIxIn0.oyHeGl5nb7ScrFGpp5MTE-0mtYYiybka6jWvhnq0wnA",
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzc1NzIzNTEzLCJpYXQiOjE3NzU3MjMyMTQsImp0aSI6Ijg5NDE3NzhiMjYzMTQxMTY4ZjYyZjc3Y2E0M2NlZmY1IiwidXNlcl9pZCI6IjEifQ.Gw2sMg_3kOP36aJbgpWpLU-Dnndg_c8xaN2WO2obQdc"
}
```

#### Refresh Token

```
POST /api/token/refresh/
Content-Type: application/json

{
  "refresh": "your_refresh_token"
}
```

For authenticated requests, include the access token in the Authorization header:

```
Authorization: Bearer <access_token>
```

### Endpoints

All API endpoints are prefixed with `/api/v1/`.

#### Students

##### List All Students (Public)

```
GET /api/v1/student-list/
```

- **Method**: GET
- **Authentication**: Not required
- **Response**: List of all students

##### List/Create Students (Authenticated)

```
GET /api/v1/students/
POST /api/v1/students/
```

- **GET Method**: Retrieve all students
- **POST Method**: Create a new student
- **Authentication**: Required
- **POST Body**:
  ```json
  {
    "name": "John Doe",
    "age": 20,
    "email": "john.doe@example.com",
    "course": 1
  }
  ```
- **Response (GET)**: Array of student objects
- **Response (POST)**: Created student object

##### Student Details (Authenticated)

```
GET /api/v1/students/<id>/
PUT /api/v1/students/<id>/
DELETE /api/v1/students/<id>/
```

- **GET**: Retrieve a specific student
- **PUT**: Update a student
- **DELETE**: Delete a student
- **Authentication**: Required
- **PUT Body**: Same as POST body for creation
- **Response**: Student object (GET/PUT) or empty (DELETE)

#### Courses

##### List All Courses (Public)

```
GET /api/v1/course-list/
```

- **Method**: GET
- **Authentication**: Not required
- **Response**: List of all courses

##### List/Create Courses (Authenticated)

```
GET /api/v1/courses/
POST /api/v1/courses/
```

- **GET Method**: Retrieve all courses
- **POST Method**: Create a new course
- **Authentication**: Required
- **POST Body**:
  ```json
  {
    "name": "Computer Science 101"
  }
  ```
- **Response (GET)**: Array of course objects
- **Response (POST)**: Created course object

##### Course Details (Authenticated)

```
GET /api/v1/courses/<id>/
PUT /api/v1/courses/<id>/
DELETE /api/v1/courses/<id>/
```

- **GET**: Retrieve a specific course
- **PUT**: Update a course
- **DELETE**: Delete a course
- **Authentication**: Required
- **PUT Body**: Same as POST body for creation
- **Response**: Course object (GET/PUT) or empty (DELETE)

### Data Models

#### Student

```json
{
  "id": 1,
  "name": "John Doe",
  "age": 20,
  "email": "john.doe@example.com",
  "course": 1,
  "created_at": "2023-01-01T00:00:00Z",
  "updated_at": "2023-01-01T00:00:00Z"
}
```

#### Course

```json
{
  "id": 1,
  "name": "Computer Science 101",
  "created_at": "2023-01-01T00:00:00Z",
  "updated_at": "2023-01-01T00:00:00Z"
}
```

## Development

### Code Quality

This project uses several tools for code quality:

- **Ruff**: Linting and formatting
- **MyPy**: Type checking
- **Pre-commit**: Git hooks for code quality

Run code quality checks:

```bash
pre-commit run --all-files
```

### Testing

Run tests:

```bash
uv run pytest
```

### Database

The project uses SQLite by default.
