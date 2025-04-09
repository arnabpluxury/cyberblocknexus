from app import create_app  # If using factory pattern
application = create_app()

if __name__ == "__main__":
    application.run()