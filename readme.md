## Steps to setup enviorment

1) Create a virtual enviornment (Only the first time)

```python -m venv venv```

2) Activate the virtual enviornment

```venv\Scripts\activate```

3) Install deps 

```pip install -r requirements.txt```


## Steps to run the code 

1) Add manim code to main.py

2) Run this command (Replace the YourClassName with the class name used in your code) - 

```manim -pqh app/main.py YouClassName --media_dir output```

3) The result will be stored in the ./output directory 



