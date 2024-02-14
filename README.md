## Setup

### Installation Steps (old version)

1. Clone this repository using `git clone`, and `cd` to the new directory.

1. Build the developer environment:
    ```sh
    make dev_env
    ```

1. Create a .env file, containing the following:
    ```sh
    OPENAI_API_KEY="sk-..."
    ```
    replace the `sk-...` with your own OpenAI API key.

1. Run the flask application.
    ```sh
    python app.py
    ```

1. Open a web browser and navigate to `localhost:5000`.

### New version (coming soon)

I am working on a more flexible framework for testing, that involves API calls. 
I have included the API, but it currently can only be run locally and is not 
fully implemented.

To try it:

- follow steps 1-3 above. Also add the following line to your `.env` file:
  ```sh
  # .env 
  DG_API_KEY="..."
  ```
  Replace the `...` with your own DeepGram API key.

- run the following flask application:
  ```sh
  python api.py
  ```

- navigate to `localhost:5000`, and you can interact with the API.