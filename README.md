# Grocery List Application

A Django application for managing multiple grocery lists with analytics.

## Features

- Create and manage multiple grocery lists
- Add items to lists
- Mark items as purchased
- Input price and quantity for purchased items
- Track spending and shopping patterns with analytics
- Responsive UI with Tailwind CSS

## Docker Setup

This application can be run using Docker and Docker Compose.

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/install/)

### Environment Variables

Create a `.env` file in the root directory with the following variables:

```
DEBUG=0
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=localhost,127.0.0.1
DATABASE_URL=postgres://postgres:postgres@db:5432/groceries
REDIS_URL=redis://redis:6379/0
```

### Running the Application

1. Build and start the containers:

```bash
docker-compose up -d
```

2. Create a superuser:

```bash
docker-compose exec web python manage.py createsuperuser
```

3. Access the application at http://localhost:8000

### Stopping the Application

```bash
docker-compose down
```

To remove all data (including the database):

```bash
docker-compose down -v
```

## Development Setup

If you prefer to run the application without Docker:

1. Create a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Set up environment variables in a `.env` file

4. Run migrations:

```bash
python manage.py migrate
```

5. Create a superuser:

```bash
python manage.py createsuperuser
```

6. Run the development server:

```bash
python manage.py runserver
```

7. Access the application at http://localhost:8000

## Project Structure

- `groceries/` - Main Django project directory
- `lists/` - Django app for grocery list functionality
- `static/` - Static files (CSS, JavaScript)
- `templates/` - HTML templates
- `media/` - User-uploaded files

## Technologies Used

- Django
- PostgreSQL
- Redis
- Tailwind CSS
- Chart.js
- Docker 