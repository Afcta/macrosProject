#### MacroTracker9000
### What is MacroTracker9000 all about?
MacroTracker9000 is what it sounds like. An app made to track your macro-nutrients from the foods you eat on a day-to-day basis.
It allows you to track foods and grouping them into the meals you've eaten. There is also a calendar with the foods you ate.
The data regarding the food items come from databases from USDA FoodData Central (**https://fdc.nal.usda.gov/**)

### How to run the app
**Note:** The app is an android and pc app but is right now only available for pc until I get a proper software license for my app. 
## _Prerequisites:_ You need to have git installed
## 1: Install uv (if you don't have it)
If you use Linux / macOS you can open a terminal and type either: 
-`pipx install uv`
or
-`pip install uv`

If you have curl either or wget you can also use: 
`curl -LsSf https://astral.sh/uv/install.sh | sh`
or
-`wget -qO- https://astral.sh/uv/install.sh | sh`

If you use Windows you can open your terminal and run:
If on powershell:
`powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"`
If on WinGet:
`winget install --id=astral-sh.uv -e`
Now close and open a new terminal.

## 2: Install Python 
This project uses Python 3.13. If you don't have Python 3.13, uv can install it for you:
`uv python install 3.13`

## 3: Clone the project
`git clone https://github.com/Afcta/macrosProject.git`

## 4: Run the app
`uv run src/uv_macrosproject/main.py`

uv will automatically create and manage the project's virtual environment and its dependencies.
