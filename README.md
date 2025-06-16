# Real-Time Delphi (RTD) Web Application

This web application facilitates Real-Time Delphi (RTD) studies, allowing researchers to conduct expert surveys with immediate, dynamic feedback to participants. Unlike traditional multi-round Delphi studies, this method is "round-less." Experts receive updated group statistics in real-time as soon as other participants submit or change their answers.

## Overview

The application supports two main user roles:

*   **Administrator (Researcher):** Sets up and manages studies, creates questionnaires, invites experts, monitors progress, and accesses final results.
*   **Expert (Participant):** Participates in studies by providing numerical assessments and qualitative justifications. Experts see anonymous, aggregated group responses in real-time and can revise their answers.

Key features include study creation, question building (scale and open-ended), participant access code generation, real-time feedback panels for experts (group statistics and qualitative reasons), and results visualization for administrators.

## Prerequisites

Before you begin, ensure you have the following installed on your system:

*   **Python:** Version 3.8 or higher is recommended.
    *   You can download Python from [python.org](https://www.python.org/downloads/).
    *   During installation, make sure to check the box that says "Add Python to PATH" (especially on Windows).
*   **Git:** Required for cloning the repository and managing updates.
    *   You can download Git from [git-scm.com](https://git-scm.com/downloads/).
*   **pip:** Python's package installer. It usually comes with Python installations (version 3.4+).
*   **(Optional) PostgreSQL:** While the application defaults to using SQLite (which requires no separate installation), for a production environment, you might consider using PostgreSQL. If you choose to use PostgreSQL, you will need to install it separately and configure the `SQLALCHEMY_DATABASE_URI` in `config.py`. Instructions for PostgreSQL setup are beyond the scope of this README.

Ensure that `python` (or `python3` on some systems) and `git` commands are accessible from your terminal or command prompt. You can check this by typing `python --version` (or `python3 --version`) and `git --version`.

## Getting Started

Follow these steps to get the application running on your local machine.

**1. Clone the Repository**

First, clone the project repository to your local machine using Git. Open your terminal or command prompt and run:

```bash
git clone <your-repository-url-here>
```
*(Replace `<your-repository-url-here>` with the actual URL of this repository.)*

Navigate into the cloned project directory:

```bash
cd your-repository-name
```
*(Replace `your-repository-name` with the actual directory name, e.g., `rtd-app`.)*

The following sections provide OS-specific instructions for setting up the environment, installing dependencies, and running the application.

### Windows

Follow these steps to set up and run the application on Windows:

**2. Create and Activate a Virtual Environment**

It's highly recommended to use a virtual environment to manage project dependencies.

```bash
python -m venv venv
.\venv\Scripts\activate
```
After activation, your command prompt should be prefixed with `(venv)`.

**3. Install Dependencies**

Install the required Python packages using pip:

```bash
pip install -r requirements.txt
```

**4. Initialize the Database**

Set the `FLASK_APP` environment variable and then initialize the database.

```bash
set FLASK_APP=rtd_app\run.py
flask db init
flask db migrate -m "Initial database setup"
flask db upgrade
```
*   If you encounter an error like "Error: Could not locate Flask application," ensure you are in the project's root directory and that `FLASK_APP` is set correctly to point to the `run.py` file within the `rtd_app` directory.
*   The `flask db init` command is only needed if the `migrations` directory is not present. If it exists, you can skip it.
*   The `flask db migrate -m "Initial database setup"` command is generally needed only if you are setting up migrations from scratch (e.g., the `migrations/versions` directory is empty or you just ran `flask db init`). If the repository already contains migration scripts, you can usually skip `flask db init` and `flask db migrate`, and proceed directly to `flask db upgrade`. If unsure, running `flask db upgrade` first will tell you if the database is uninitialized or if migrations are pending.

**5. Create an Administrator User**

You'll need an administrator account to manage studies. Use the following command, replacing `<your_username>` and `<your_password>` with your desired credentials:

```bash
flask create-admin <your_username> <your_password>
```
Example: `flask create-admin admin securepassword123`

**6. Run the Application**

Start the Flask development server:

```bash
python rtd_app\run.py
```
*(This assumes `run.py` uses `socketio.run(app, ...)` for Flask-SocketIO. If it uses `app.run(...)`, then `flask run` would be the command, but `python rtd_app\run.py` is generally safer for SocketIO applications when `run.py` is structured to handle it).*

Once the server is running, you should see output indicating it's serving on `http://127.0.0.1:5000/` (or a similar address). You can access the application by opening this URL in your web browser.

### macOS

Follow these steps to set up and run the application on macOS:

**2. Create and Activate a Virtual Environment**

Using a virtual environment is crucial for managing project dependencies.

```bash
python3 -m venv venv
source venv/bin/activate
```
After activation, your terminal prompt should be prefixed with `(venv)`. If `python3` is not found, try `python -m venv venv`.

**3. Install Dependencies**

Install the required Python packages:

```bash
pip install -r requirements.txt
```

**4. Initialize the Database**

Set the `FLASK_APP` environment variable and then initialize the database.

```bash
export FLASK_APP=rtd_app/run.py
flask db init
flask db migrate -m "Initial database setup"
flask db upgrade
```
*   If you encounter an error like "Error: Could not locate Flask application," ensure you are in the project's root directory and that `FLASK_APP` is set correctly to point to the `run.py` file within the `rtd_app` directory.
*   The `flask db init` command is only needed if the `migrations` directory is not present. If it exists, you can skip it.
*   The `flask db migrate -m "Initial database setup"` command is generally needed only if you are setting up migrations from scratch (e.g., the `migrations/versions` directory is empty or you just ran `flask db init`). If the repository already contains migration scripts, you can usually skip `flask db init` and `flask db migrate`, and proceed directly to `flask db upgrade`. If unsure, running `flask db upgrade` first will tell you if the database is uninitialized or if migrations are pending.

**5. Create an Administrator User**

Create an administrator account to manage studies. Replace `<your_username>` and `<your_password>` with your chosen credentials:

```bash
flask create-admin <your_username> <your_password>
```
Example: `flask create-admin admin securepassword123`

**6. Run the Application**

Start the Flask development server:

```bash
python rtd_app/run.py
```
*(This assumes `run.py` uses `socketio.run(app, ...)` for Flask-SocketIO. If it uses `app.run(...)`, then `flask run` would be the command, but `python rtd_app/run.py` is generally safer for SocketIO applications when `run.py` is structured to handle it).*

The application should now be running on `http://127.0.0.1:5000/`. Open this URL in your web browser.

### Linux

Follow these steps to set up and run the application on Linux:

**2. Create and Activate a Virtual Environment**

Using a virtual environment is highly recommended.

```bash
python3 -m venv venv
source venv/bin/activate
```
*   If `python3` is not found, try `python -m venv venv`.
*   You might need to install the `python3-venv` package first if it's not available on your distribution (e.g., `sudo apt update && sudo apt install python3-venv` on Debian/Ubuntu).

**3. Install Dependencies**

Install the required Python packages. You may need to install `python3-dev` or `build-essential` if you encounter errors during the installation of certain packages (like `psycopg2-binary` if you were to use PostgreSQL).

```bash
pip install -r requirements.txt
```

**4. Initialize the Database**

Set the `FLASK_APP` environment variable and then initialize the database.

```bash
export FLASK_APP=rtd_app/run.py
flask db init
flask db migrate -m "Initial database setup"
flask db upgrade
```
*   If you encounter an error like "Error: Could not locate Flask application," ensure you are in the project's root directory and that `FLASK_APP` is set correctly to point to the `run.py` file within the `rtd_app` directory.
*   The `flask db init` command is only needed if the `migrations` directory is not present. If it exists, you can skip it.
*   The `flask db migrate -m "Initial database setup"` command is generally needed only if you are setting up migrations from scratch (e.g., the `migrations/versions` directory is empty or you just ran `flask db init`). If the repository already contains migration scripts, you can usually skip `flask db init` and `flask db migrate`, and proceed directly to `flask db upgrade`. If unsure, running `flask db upgrade` first will tell you if the database is uninitialized or if migrations are pending.

**5. Create an Administrator User**

Create an administrator account. Replace `<your_username>` and `<your_password>` with your desired credentials:

```bash
flask create-admin <your_username> <your_password>
```
Example: `flask create-admin admin securepassword123`

**6. Run the Application**

Start the Flask development server:

```bash
python rtd_app/run.py
```
*(This assumes `run.py` uses `socketio.run(app, ...)` for Flask-SocketIO. If it uses `app.run(...)`, then `flask run` would be the command, but `python rtd_app/run.py` is generally safer for SocketIO applications when `run.py` is structured to handle it).*

The application will typically be available at `http://127.0.0.1:5000/`. Open this URL in your web browser.

## Updating the Application

To update the application to the latest version, follow these steps:

1.  **Navigate to Project Directory:**
    Open your terminal or command prompt and navigate to the project's root directory.

    ```bash
    cd path/to/your-repository-name
    ```
    *(Replace `path/to/your-repository-name` with the actual path to your project.)*

2.  **Activate Virtual Environment:**
    Ensure your project's virtual environment is activated.

    *   **Windows:**
        ```bash
        .\venv\Scripts\activate
        ```
    *   **macOS & Linux:**
        ```bash
        source venv/bin/activate
        ```

3.  **Pull Latest Changes:**
    Fetch the latest code from the repository. If you are on the `main` branch (or your primary development branch), you can use:

    ```bash
    git pull origin main
    ```
    If you are working on a different branch, replace `main` with your branch name.

4.  **Update Dependencies:**
    Install or update any changed Python packages:

    ```bash
    pip install -r requirements.txt
    ```

5.  **Apply Database Migrations:**
    If there have been changes to the database schema, apply them:

    ```bash
    # Ensure FLASK_APP is set (e.g., export FLASK_APP=rtd_app/run.py or set FLASK_APP=rtd_app\run.py for Windows)
    flask db upgrade
    ```

6.  **Restart the Application:**
    If the application was running, stop it (usually `Ctrl+C` in the terminal) and restart it to apply all changes:

    ```bash
    python rtd_app/run.py
    ```
    (Or `flask run` if applicable, ensuring `FLASK_APP` is set correctly)

By following these steps, your local instance of the application will be updated with the latest features, bug fixes, and dependency changes.

## Running the Application

Once you have completed the setup steps for your operating system (see the "[Getting Started](#getting-started)" section), you can run the application using the following general steps:

1.  **Navigate to Project Directory:**
    Open your terminal or command prompt and ensure you are in the project's root directory (e.g., `your-repository-name`).

2.  **Activate Virtual Environment:**
    *   **Windows:** `.\venv\Scripts\activate`
    *   **macOS & Linux:** `source venv/bin/activate`

3.  **Start the Server:**
    Use the command appropriate for this application (which includes Flask-SocketIO):

    ```bash
    python rtd_app/run.py
    ```
    You should see output in your terminal indicating that the development server is running, typically on `http://127.0.0.1:5000/`.

4.  **Access the Application:**
    Open your web browser and navigate to the address shown in the terminal (usually `http://127.0.0.1:5000/`).

    *   The administrator interface is typically available at `/admin` (e.g., `http://127.0.0.1:5000/admin`).
    *   Survey access links for participants will be generated by the administrator within a study.

To stop the server, press `Ctrl+C` in the terminal where it's running.

## Basic Usage

Here's a brief overview of how to use the application's core features:

**1. Administrator Access:**

*   Navigate to the admin login page, typically `http://127.0.0.1:5000/admin/login`.
*   Log in with the administrator credentials you created during setup (using the `flask create-admin` command).

**2. Managing Studies (as Administrator):**

*   **Create a New Study:**
    *   From the admin dashboard (e.g., `/admin/studies`), click on "Create New Study."
    *   Fill in the study title, description, start date, and end date.
    *   Click "Create Study."
*   **View Study Details:**
    *   Click on a study title from the list to go to its detail page.
*   **Add Questions to a Study:**
    *   On the study detail page, click "Add New Question."
    *   Enter the question text.
    *   Select the question type: "Scale" (for numerical ratings) or "Open-Ended" (for text justifications).
    *   If "Scale" is chosen, specify the minimum and maximum values for the scale.
    *   Click "Add Question."
*   **Generate Participant Access Codes:**
    *   On the study detail page, find the "Participant Management" section.
    *   Enter the number of participants you want to generate codes for.
    *   Click "Generate Participants." Unique access codes will be created and listed. Distribute these codes (or the full access links `http://127.0.0.1:5000/survey/<code>`) to your expert participants.

**3. Expert Participation:**

*   Experts receive a unique access code from the administrator.
*   They access the survey by navigating to `http://127.0.0.1:5000/survey/<access_code>` (replacing `<access_code>` with their actual code).
*   **Answering Questions:**
    *   For each question, provide a numerical rating (if applicable) and a qualitative justification in the text box.
    *   View real-time feedback from other participants (average, median, count for scale questions, and anonymous qualitative reasons).
*   **Submitting and Revising Answers:**
    *   Click "Save Answers" to submit or update responses.
    *   Experts can revisit the survey using their access code and revise their answers as many times as needed before the study's end date. The feedback panel will update for all participants in real-time.

**4. Viewing Results (as Administrator):**

*   After a study has progressed or concluded, navigate to the study detail page.
*   Click on "View Results & Export Data."
*   **View Aggregated Data:**
    *   Bar charts will display the distribution of final numerical answers for scale questions.
    *   A list of all qualitative justifications for each question will be shown.
*   **Export Data:**
    *   Click "Export Results as CSV" to download all survey data for offline analysis.

This provides a basic workflow. Explore the interface for further details and options.

## Contributing

(Placeholder - Optional)
We welcome contributions! Please see `CONTRIBUTING.md` for details (if such a file exists).

## License

(Placeholder - Optional)
This project is licensed under the MIT License - see the `LICENSE` file for details (if such a file exists).
```
