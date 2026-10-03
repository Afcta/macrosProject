import json
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.widget import Widget
from kivy.uix.popup import Popup
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.spinner import Spinner
import datetime 
import os
import calendar
from datetime import date

#For the android
from kivy.utils import platform
from pathlib import Path
from kivy.metrics import dp
import shutil
from kivy.resources import resource_find

#For string operations
import string
from rapidfuzz.distance import Levenshtein
# import numpy as np
# from scipy.optimize import linear_sum_assignment

# if platform == "android":
#     base = Path("/sdcard/MyApp")
# else:
#     base = Path("MealLogs")
BASE_DIR = None
_BASE = None

def get_base():
    global _BASE
    if _BASE is not None:
        return _BASE

    if platform == "android":
        try:
            from android.storage import app_storage_path
            base = Path(app_storage_path()) / "MealLogs"
        except Exception:
            base = Path("/sdcard/MealLogs")
    else:
        base = Path("MealLogs")

    base.mkdir(parents=True, exist_ok=True)
    _BASE = base
    return base

# ====================== CALENDAR SCREEN ======================
class CalendarScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_date = datetime.date.today().replace(day=1)  # Start at 1st of current month
        self.build_ui()

    def build_ui(self):
        main_layout = BoxLayout(orientation='vertical')

        # Top Bar
        top_bar = BoxLayout(size_hint_y=None, height=dp(60), padding=dp(10), spacing=dp(10))
        
        prev_btn = Button(text="< Previous", size_hint_x=0.3)
        prev_btn.bind(on_press=self.prev_month)
        
        self.month_label = Label(text="", font_size=20, bold=True)
        
        next_btn = Button(text="Next >", size_hint_x=0.3)
        next_btn.bind(on_press=self.next_month)

        top_bar.add_widget(prev_btn)
        top_bar.add_widget(self.month_label)
        top_bar.add_widget(next_btn)

        # Calendar Grid
        self.calendar_grid = GridLayout(cols=7, spacing=dp(5), padding=dp(10), size_hint_y=None)
        self.calendar_grid.bind(minimum_height=self.calendar_grid.setter('height'))

        # Meal List Area
        self.meal_scroll = ScrollView()
        self.meal_list = BoxLayout(orientation='vertical', size_hint_y=None, spacing=dp(8))
        self.meal_list.bind(minimum_height=self.meal_list.setter('height'))
        self.meal_scroll.add_widget(self.meal_list)

        # Back Button
        back_btn = Button(text="Back to Search", size_hint_y=None, height=dp(50))
        back_btn.bind(on_press=self.go_back)

        main_layout.add_widget(top_bar)
        main_layout.add_widget(self.calendar_grid)
        main_layout.add_widget(self.meal_scroll)
        main_layout.add_widget(back_btn)

        self.add_widget(main_layout)
        self.build_calendar()

    def build_calendar(self):
        self.calendar_grid.clear_widgets()
        self.meal_list.clear_widgets()

        # Weekday headers
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        for d in days:
            self.calendar_grid.add_widget(Label(text=d, bold=True, size_hint_y=None, height=dp(40)))

        # Get calendar matrix
        cal = calendar.monthcalendar(self.current_date.year, self.current_date.month)

        for week in cal:
            for day_num in week:
                if day_num == 0:
                    self.calendar_grid.add_widget(Widget())
                    continue

                current_day = date(self.current_date.year, self.current_date.month, day_num)
                has_meals = self.has_logged_meals(current_day)

                btn = Button(
                    text=str(day_num),
                    size_hint_y=None,
                    height=dp(55),
                    background_color=(0.2, 0.8, 0.8, 0.6) if has_meals else (0.4, 0.4, 0.4, 0.8)
                )
                def make_callback(d):
                    return lambda instance: self.show_meals(d)

                btn.bind(on_press=make_callback(current_day))
                # btn.bind(on_press=lambda instance, d=current_day: self.show_meals(d))
                self.calendar_grid.add_widget(btn)

        self.month_label.text = self.current_date.strftime("%B %Y")

    def has_logged_meals(self, check_date):
        filepath = (get_base()) / f"MealLog_{check_date}.json"
        return (filepath).exists()

    def show_meals(self, selected_date):
        self.meal_list.clear_widgets()

        title = Label(text=f"Meals on {selected_date.strftime('%A, %d %B %Y')}", 
                      size_hint_y=None, height=dp(50), bold=True)
        self.meal_list.add_widget(title)

        filepath = (get_base()) / f"MealLog_{selected_date}.json"
        
        if (filepath).exists():
            data = {}
            with open(filepath, "r") as f:
                data = json.load(f)

            if "<Total>" in data.keys():
                cals = data["<Total>"]["calories"]
                protein = data["<Total>"]["protein"]
                carbs = data["<Total>"]["carbs"]
                fat = data["<Total>"]["fat"]
                meal_label = Label(
                    text=f"<Total>: {round(cals,1)} kcal | {round(protein,1)}g protein | {round(carbs,1)}g carbs | {round(fat,1)}g fat",
                    size_hint_y=None, height=dp(40), halign="left", valign="middle"
                )
                meal_label.bind(width=lambda inst, w: setattr(inst, "text_size", (w - dp(20), None)))
                meal_label.color="red"
                self.meal_list.add_widget(meal_label)

            for key, value in data.items():
                if key == "<Total>":
                    continue
                foods = [foodQty for foodQty in value["foodQuantities"]]
                print("Log: foods = "+str(foods))
                # foods = value[0]
                cals = value["calories"]
                protein = value["protein"]
                carbs = value["carbs"]
                fat = value["fat"]

                meal_label = Label(
                    text=f"{key}: {cals} kcal | {protein}g protein | {carbs}g carbs | {fat}g fat",
                    size_hint_y=None, height=dp(40), halign="left"
                )
                meal_label.bind(width=lambda inst, w: setattr(inst, "text_size", (w - dp(20), None)))
                self.meal_list.add_widget(meal_label)

                for food in foods:
                    item_label = Label(
                        text=f"   • {food['qty']} {food['portionName']} × {food['name']}",
                        size_hint_y=None, height=dp(30), halign="left"
                    )
                    item_label.bind(width=lambda inst, w: setattr(inst, "text_size", (w - dp(20), None)))
                    self.meal_list.add_widget(item_label)

        else:
            self.meal_list.add_widget(Label(text="No meals logged on this day.", size_hint_y=None, height=dp(50)))

    def prev_month(self, instance):
        if self.current_date.month == 1:
            self.current_date = self.current_date.replace(year=self.current_date.year - 1, month=12)
        else:
            self.current_date = self.current_date.replace(month=self.current_date.month - 1)
        self.build_calendar()

    def next_month(self, instance):
        if self.current_date.month == 12:
            self.current_date = self.current_date.replace(year=self.current_date.year + 1, month=1)
        else:
            self.current_date = self.current_date.replace(month=self.current_date.month + 1)
        self.build_calendar()

    def go_back(self, instance):
        self.manager.current = "search"

class SearchScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        app = App.get_running_app()
        self.search_ui = SearchUI(app.foodList, app.selectedFoods)
        self.add_widget(self.search_ui)

class DetailScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        main_layout = BoxLayout(orientation="vertical", spacing=dp(30))
        # self.food_list = GridLayout(cols=1, spacing=10)

        app = App.get_running_app()
        self.todaysFoods=app.todaysFoods
        # print("TODAYS FOODS= ",self.todaysFoods)
        self.selectedFoods = app.selectedFoods
        self.foodList = app.foodList
        self.food_counts1 = {}
        self.food_rows = {}

        selectFoodScroll = ScrollView(size_hint_y=None, height=dp(200))

        self.selectFoodGrid = GridLayout(size_hint_y=None, cols=1) #Food label | number input
        self.selectFoodGrid.bind(minimum_height=self.selectFoodGrid.setter("height"))
        selectFoodScroll.add_widget(self.selectFoodGrid)
        self.update_select_food_grid()
        main_layout.add_widget(selectFoodScroll)

        todaysFoodBox = BoxLayout(orientation="vertical", size_hint_y=0.1)
        scroll = ScrollView(size_hint_y=None, height=dp(200))
        todaysFoodBox.add_widget(Label(text="Todays Foods:", valign="bottom"))
        todaysFoodBox.add_widget(scroll)

        self.label = Label(text="No food selected")

        self.food_list = GridLayout(cols=1, spacing=dp(10), size_hint_y=None)
        self.food_listToday = GridLayout(cols=1, spacing=dp(10), size_hint_y=None)
        self.food_listToday.bind(minimum_height=self.food_listToday.setter('height'))
        self.update_todays_food()

        scroll.add_widget(self.food_listToday)

        self.totalCals = None
        self.totalProtein = None
        self.totalCarbs = None
        self.totalFat = None

        # main_layout.add_widget(self.food_list)

        self.options_grid = GridLayout(cols=1, size_hint_y=None, height=dp(150), pos_hint={"center_x":0.5, "center_y":0.3})
        back_btn = Button(text="Back", size_hint_y=0.5)
        back_btn.bind(on_press=self.go_back)
        self.options_grid.add_widget(back_btn)

        add_items_btn = Button(text="Log meal", size_hint_y=0.5)
        add_items_btn.bind(on_press=self.on_add_food_item_number)
        self.options_grid.add_widget(add_items_btn)
        main_layout.add_widget(self.options_grid)
        self.add_widget(main_layout)
        main_layout.add_widget(todaysFoodBox)

    def go_back(self, instance):
        self.manager.current = "search"

    def update_select_food_grid(self):
        print("LOG: UPDATING SELECT FOOD GRID")
        print("LOG1: self.selectedFoods IS "+str(self.selectedFoods) )
        self.selectFoodGrid.clear_widgets()

        def macroInfoPopup(instance, name, cal, prot, carbs, fat):
            layout = BoxLayout(orientation="vertical", spacing=dp(10), padding=dp(10))
            layout.add_widget(Label(text=f"{name}\n{cal} kcal\n{prot}g protein\n{carbs}g carbs\n{fat}g fat"))
            btn = Button(text="Back", size_hint_y=None, height=dp(40))
            layout.add_widget(btn)
            popup = Popup(title="Food Info", content=layout, size_hint=(0.6, 0.4))
            btn.bind(on_press=popup.dismiss)
            popup.open()
            
        for foodEntry in self.selectedFoods:
            name = foodEntry["name"]
            # value = self.selectedFoods[name]
            fr = FoodRow(name, foodEntry["cals"], foodEntry["protein"], foodEntry["carbs"], foodEntry["fat"], foodEntry["portions"])
            print("Log fr portions field:",foodEntry["portions"])
            fr.clickableLabel.bind(on_press=lambda instance, name=name, cals=foodEntry["cals"], prot=foodEntry["protein"], carbs=foodEntry["carbs"], fat=foodEntry["fat"]: macroInfoPopup(instance, name, cals, prot, carbs, fat))
            self.selectFoodGrid.add_widget(fr)
            print("Log: selectedFoods:", self.selectedFoods)
            # print("Log: foodPortions: ", foodEntry["foodPortions"])
            # self.food_rows.append(fr)

    def update_todays_food(self):
        """Updates the detail screen\'s \"today's foods buttons\""""
        print("LOG: UPDATING TODAYS FOODS")
        app = App.get_running_app()
        todaysFoodsPath = (get_base()) / f"MealLog_{datetime.date.today()}.json"
        
        app.todaysFoods = {}
        self.todaysFoods = {}
        if (todaysFoodsPath).exists():
            with open(todaysFoodsPath, "r") as f:
                app.todaysFoods = json.load(f)
                self.todaysFoods = app.todaysFoods
        print("LOG: TODAYS FOODS:",self.todaysFoods)
        self.food_listToday.clear_widgets()
        if "<Total>" in self.todaysFoods:
            # totalCalToday, totalProtToday = self.todaysFoods["<Total>"]
            totalCalToday = self.todaysFoods["<Total>"]["calories"]
            totalProtToday = self.todaysFoods["<Total>"]["protein"]
            totalCarbsToday = self.todaysFoods["<Total>"]["carbs"]
            totalFatToday = self.todaysFoods["<Total>"]["fat"]
            text = "Total: "+str(round(totalCalToday, 1))+"Kcal, "+str(round(totalProtToday,1))+" Protein, "+str(round(totalCarbsToday,1))+" Carbs, "+str(round(totalFatToday,1))+" Fat"
            todayBtn = Label(text=text, color="red", size_hint_y=None, height=dp(80), halign="left")
            todayBtn.bind(width=lambda inst, w: setattr(inst, "text_size", (w - dp(20), None)))
            self.food_listToday.add_widget(Label(text=text, color="red", size_hint_y=None, height=dp(80), halign="left"))
        for key in self.todaysFoods:
            # Meal = key[1:-1]
            # qty,  = self.todaysFoods[key][0][0]
            # text = key+": "+str(self.todaysFoods[key][])
            if key == "<Total>": continue
            textParts = []
            for mealList in self.todaysFoods[key]["foodQuantities"]:
                # mealList = self.todaysFoods[key]["foodQuantities"]
                # # for food, number in mealList: #FoodNumber is like ["food", n]
                # #     text += str(number)+" "+food
                print("MEALLIST:",mealList)
                name = mealList["name"]
                qty = mealList["qty"]
                portionName = mealList["portionName"]
                # text = key+": "+", ".join(
                #     f"{qty} {portionName} {name}"
                # )    
                #FIXFIX
                text1 = f"{qty} {portionName} × {name}"
                textParts.append(text1)
                #Item looks like [["food", n], ["food", n]]
                #We want text = smt like "meal1: 3 butter, 2 meat. 500 cals, 60 prot"
                # text += text1
            text = f"{key}: "+" , ".join(textParts) +":"

            cals = self.todaysFoods[key]["calories"]
            prot = self.todaysFoods[key]["protein"] 
            carbs = self.todaysFoods[key]["carbs"] 
            fat = self.todaysFoods[key]["fat"] 
            text += "\n"+str(prot)+"g Protein, " + str(cals)+" Kcal, "+str(carbs)+" Carbs, "+str(fat)+" Fat"

            button = Button(size_hint_y=None, height=dp(80),text=text, halign="left")#str(self.todaysFoods[key]))
            button.bind(size=lambda instance, value: setattr(instance, 'text_size', (instance.width - dp(10), None)))
            button.meal_name = key
            button.bind(on_press=self.on_delete_meal)
            self.food_listToday.add_widget(button)

    # def add_food_widget_number(self, name, cal, protein):
    #     row = BoxLayout(orientation="horizontal", size_hint_y=None, size_hint_x=0.2, height=40)

    #     new_label = Label(text=f"{name} - {cal} kcal - {protein}g protein", size_hint_x=0.7)
        
    #     number_input = TextInput(text="1", multiline=False, size_hint_x=0.2)
    #     self.food_counts[name] = number_input

    #     row.add_widget(new_label)
    #     row.add_widget(number_input)
        
    #     self.food_list.add_widget(row)

    def on_add_food_item_number(self, instance):
        # app = App.get_running_app()
        # search_screen = app.root.get_screen("search")
        # search_ui = search_screen.children[0]
        totalCals = 0
        totalProtein = 0
        totalCarbs = 0
        totalFat = 0
        app = App.get_running_app()
        foodList = app.foodList

        # for fr in self.food_rows:
        if not self.selectFoodGrid.children: return
        for fr in reversed(self.selectFoodGrid.children):
            name = fr.name
            qty = fr.get_quantity()
            foodGramWeight = fr.get_foodPortion_grams()
            foodGramWeight = foodGramWeight*qty
            # foodEntry = [foodEntry for foodEntry in foodList if foodEntry["name"] == name]
            foodEntry = next((foodEntry for foodEntry in foodList if foodEntry["name"] == name), None)
            if foodEntry:
                cal, protein, carbs, fat = foodEntry["cals"], foodEntry["protein"], foodEntry["carbs"], foodEntry["fat"]
                totalCals += cal*(foodGramWeight/100)
                totalProtein += protein*(foodGramWeight/100)
                totalCarbs += carbs*(foodGramWeight/100)
                totalFat += fat*(foodGramWeight/100)
            else:
                print("WARNING, NAME NOT IN FOOD DICT!!")

        # for name, input_box in self.food_counts.items():
        #     qty = int(input_box.text)
        #     print(name, qty)
        #     if name in foodList:
        #         cal, protein = foodList[name]
        #         totalCals += cal*qty
        #         totalProtein += protein*qty
        self.totalCals = totalCals
        self.totalProtein = totalProtein
        self.totalCarbs = totalCarbs
        self.totalFat = totalFat

        self.show_popup()
        print("Total cal, protein, carbs, fat: "+str(totalCals)+", "+str(totalProtein)+", "+str(totalCarbs)+", "+str(totalFat))


    def on_delete_meal(self, instance):
        layout = BoxLayout(orientation="vertical", spacing=dp(10), padding=dp(10))

        label = Label(text="Delete this meal?")
        layout.add_widget(label)

        btn = Button(text="Confirm", size_hint_y=None, height=dp(50))
        layout.add_widget(btn)
        
        btnNo = Button(text="Cancel", size_hint_y=None, height=dp(50))
        layout.add_widget(btnNo)

        popup = Popup(
            title="Delete Meal",
            content=layout,
            size_hint=(0.7, 0.4),
            auto_dismiss=False
        )

        def on_confirm(instance1):
            # print([self.food_counts, self.totalCals, self.totalProtein])
            
            lFoods, cals, protein = None, None, None
            data = {}
            filepath = (get_base())/f"MealLog_{datetime.date.today()}.json"
            if (filepath).exists():
                with open(filepath, "r") as f:
                    data = json.load(f)
                    # lFoods, cals, protein = json.load(f)
                    data.pop(instance.meal_name)
                    newTotalCalories, newTotalProt, newTotalCarbs, newTotalFat = 0, 0, 0, 0
                    for key in data:
                        if key == "<Total>": continue
                        newTotalCalories+=data[key]["calories"]
                        newTotalProt+=data[key]["protein"]
                        newTotalCarbs+=data[key]["carbs"]
                        newTotalFat+=data[key]["fat"]

                    if "<Total>" in data:
                        data["<Total>"] = {"calories": newTotalCalories, "protein": newTotalProt, "carbs": newTotalCarbs, "fat": newTotalFat}
                with open(filepath, "w") as f:
                    data = normalize_meals_dict(data)
                    json.dump(data, f)
                if len(data) <= 1 and os.path.exists(filepath):
                    os.remove(filepath) 
                self.update_todays_food()
            popup.dismiss()  # close popup

        btn.bind(on_press=on_confirm)
        btnNo.bind(on_press=popup.dismiss)
        popup.open()

    def show_popup(self):
        layout = BoxLayout(orientation="vertical", spacing=dp(10), padding=dp(10))

        label = Label(text="Add these foods?")
        layout.add_widget(label)

        btn = Button(text="Confirm", size_hint_y=None, height=dp(50))
        layout.add_widget(btn)
        
        btnNo = Button(text="Cancel", size_hint_y=None, height=dp(50))
        layout.add_widget(btnNo)

        popup = Popup(
            title="Add Items",
            content=layout,
            size_hint=(0.7, 0.4),
            auto_dismiss=False
        )

        def on_confirm(instance):
            # print([self.food_counts, self.totalCals, self.totalProtein])
            
            lFoods, cals, protein = None, None, None
            foodRows = self.selectFoodGrid.children
            data = {}
            if (get_base()/f"MealLog_{datetime.date.today()}.json").exists():
                with open(get_base()/f"MealLog_{datetime.date.today()}.json", "r") as f:
                    data = json.load(f)
                    # lFoods, cals, protein = json.load(f)
            mealNo = len(data) + 1
            if "<Total>" in data: mealNo-=1
            logCal, logProtein, logCarbs, logFat = 0, 0, 0, 0
            if data:
                if "<Total>" in data:
                    logCal = data["<Total>"]["calories"]
                    logProtein = data["<Total>"]["protein"]
                    logCarbs = data["<Total>"]["carbs"]
                    logFat = data["<Total>"]["fat"]
            meal_key = f"Meal{mealNo}"

            foods = []
            for fr in foodRows:
                name = fr.name
                qty = fr.get_quantity()
                portionName = fr.get_foodPortion_name_grams()[0]
                portionWeight = fr.get_foodPortion_name_grams()[1]
                portionWeight = int(portionWeight) if float(portionWeight).is_integer() else round(portionWeight, 1)
                foods.append({"name":name, "qty":qty, "portionName":portionName, "portionWeight":portionWeight})
            # foods = {"name":name, "qty":qty, "portionName":portionName, "portionWeight":portionWeight}
            # for fr in foodRows:
            #     name = fr.name
            #     qty = fr.get_quantity()
            # foods = [
            #     [name, qty]
            #     for name, qty in foodQty
            # ]
            calories = self.totalCals
            protein = self.totalProtein
            carbs = self.totalCarbs
            fat = self.totalFat
            # data[meal_key] = [foods, calories, protein, carbs, fat]
            data[meal_key] = {"foodQuantities": foods, "calories": round(calories, 1), "protein": round(protein, 1), "carbs": round(carbs, 1), "fat": round(fat, 1)}
            if "<Total>" not in data:
                data["<Total>"] = {"calories": 0, "protein": 0, "carbs": 0, "fat": 0}
            data["<Total>"]["calories"] = round(logCal + calories, 1)
            data["<Total>"]["protein"] = round(logProtein + protein, 1)
            data["<Total>"]["carbs"] = round(logCarbs + carbs, 1)
            data["<Total>"]["fat"] = round(logFat + fat, 1)
            with open(get_base()/f"MealLog_{datetime.date.today()}.json", "w") as f: # your function
                json.dump(data, f, indent=4)
            app = App.get_running_app()
            self.selectedFoods.clear()
            search_screen = app.root.get_screen("search")
            search_screen.search_ui.update_buttons(self.foodList)
            popup.dismiss()  # close popup
            self.update_todays_food()

        btn.bind(on_press=on_confirm)
        btnNo.bind(on_press=popup.dismiss)
        popup.open()

    def get_total_macros_by_meals(self, filepath):
        """Returns the total calories and Protein of a meal log, by summing each meal's written calory and protein content."""
        if os.path.exists(filepath):
            totalCalToday, totalProtToday, totalCarbsToday, totalFatToday = 0, 0, 0, 0
            foodList = None
            with open(filepath, "r") as f:
                foodList = json.load(f)
                for key in foodList:
                    if key == "<Total>": continue
                    mealCal= foodList[key]["calories"]
                    mealProt = foodList[key]["protein"]
                    mealCarbs = foodList[key]["carbs"]
                    mealFat = foodList[key]["fat"]
                    totalCalToday += mealCal
                    totalProtToday += mealProt
                    totalCarbsToday += mealCarbs
                    totalFatToday += mealFat
                foodList["<Total>"] = {"calories": totalCalToday, "protein": totalProtToday, "carbs": totalCarbsToday, "fat": totalFatToday}
            return [totalCalToday, totalProtToday, totalCarbsToday, totalFatToday]

class FoodRow(BoxLayout):
    def __init__(self, name, cal, prot, carbs, fat, portions, **kwargs):
        super().__init__(
            orientation="horizontal",
            size_hint_y=None,
            padding=dp(5),
            spacing=dp(5),
            **kwargs
        )

        self.name = name
        if "100g" not in portions: portions["100g"]=100
        self.portions = portions

        self.clickableLabel = ClickableLabel(
            text=name,
            halign="left",
            valign="middle",
            size_hint_x=0.6
        )

        self.clickableLabel.bind(
            size=lambda inst, val:
            setattr(inst, "text_size", (inst.width - dp(10), None))
        )

        self.input = TextInput(
            text="1",
            multiline=False,
            size_hint_x=0.15
        )

        self.spinner = Spinner(
            text="100g",
            values=[f"{k} ({v}g)" for k, v in portions.items()],
            size_hint_x=0.25
        )

        self.add_widget(self.clickableLabel)
        self.add_widget(self.input)
        self.add_widget(self.spinner)

        # AUTO HEIGHT
        self.bind(minimum_height=self.setter("height"))

        self.clickableLabel.bind(
            texture_size=self.update_height
        )

    def update_height(self, *args):
        self.height = max(dp(60), self.clickableLabel.texture_size[1] + dp(20))

    def get_quantity(self):
        try:
            if float(self.input.text).is_integer():
                return int(self.input.text)
            return float(self.input.text)
        except:
            return 0
        
    def get_foodPortion_grams(self):
        if self.spinner.text == "100g" or self.spinner.text == "100g": return 100
        # print("portions:",self.portions)
        # print("self.spinner.text.split()[0]:",self.spinner.text.split("(")[0])
        return self.portions[self.spinner.text.split("(")[0].rstrip()]
    
    def get_foodPortion_name_grams(self):
        if self.spinner.text == "100g" or self.spinner.text == "100g": return ["100g",100]
        return [self.spinner.text.split("(")[0].rstrip(), self.portions[self.spinner.text.split("(")[0].rstrip()]]

class SearchUI(BoxLayout):
    def __init__(self, foodList, selectedFoods, **kwargs):
        super().__init__(orientation="vertical", **kwargs)

        # # Load JSON
        # with open("organized_food_data.json", "r") as f:
        #     self.foodList = json.load(f)

        # # self.keys = list(self.foodList.keys())
        # self.foodItems = list(self.foodList.items())
        # self.selectedFoods = {}

        app = App.get_running_app()
        self.foodList = app.foodList
        # self.foodItems = list(foodList.items())
        self.selectedFoods = app.selectedFoods

        self.foodEntryTokens = {}
        translator = str.maketrans('', '', string.punctuation)
        for item in self.foodList:
            foodText = item["name"].lower()
            foodText = foodText.replace("-", " ")
            foodText = foodText.translate(translator)

            entry_tokens = foodText.split()

            if not entry_tokens:
                continue
            self.foodEntryTokens[item["name"]] = entry_tokens
        
        self.foodDict = {item["name"]: item for item in self.foodList}

        # Search bar
        self.search = TextInput(
            size_hint_y=None,
            height=dp(50),
            multiline=False,
            hint_text="Search food..."
        )
        self.search.bind(text=self.on_text)
        self.add_widget(self.search)

        # Scrollable area for buttons
        self.scroll = ScrollView()
        self.grid = GridLayout(cols=1, size_hint_y=None)
        self.grid.bind(minimum_height=self.grid.setter("height"))
        self.scroll.add_widget(self.grid)

        self.add_widget(self.scroll)

        # Create 10 buttons
        self.buttons = []
        for i in range(10):
            btn = Button(size_hint_y=None, height=dp(40), halign="left", valign="middle", padding=(dp(10),dp(10)), shorten=False)
            btn.bind(
                size=lambda inst, val:
                setattr(inst, "text_size", (inst.width - dp(20), None))
            )
            btn.bind(on_press=self.on_food_button_press) #Makes the on_food_button_press use the btn as an instance, as seen later down on "def on_food_button_press(self, instance)"
            self.buttons.append(btn)
            self.grid.add_widget(btn)
            btn.bind(
                size=lambda inst, val:
                setattr(inst, "text_size", (inst.width - dp(20), None))
            )

        self.chooseFoodBtn = Button(size_hint_y=None, height=dp(60), color="red")
        self.chooseFoodBtn.bind(on_press=self.on_choose_food_button_press)
        self.chooseFoodBtn.text = "Add/Remove (Today)"

        # self.input_number_food = TextInput(
        #     size_hint_y=None,
        #     height=dp(40),
        #     width=100,
        #     multiline=False,
        #     hint_text="Insert number of item"
        # )

        self.see_calendar = Button(size_hint_y=None, height=dp(60), color="orange", background_color="cyan")
        self.see_calendar.bind(on_press=self.on_see_calendar)
        self.see_calendar.text = "Calendar"

        self.create_new_food_btn = Button(size_hint_y=None, height=dp(60), padding=(0,0), color="white")
        self.create_new_food_btn.text = "Create new food item"
        self.create_new_food_btn.bind(on_press=self.on_create_food_button)

        self.clear_food_btn = Button(size_hint_y=None, height=dp(60), padding=(0,0), color="white")
        self.clear_food_btn.text = "Clear"
        def on_clear_food_button(instance):
            self.selectedFoods.clear()
            self.refresh_food_buttons_color()
        self.clear_food_btn.bind(on_press=on_clear_food_button)

        # self.create_food_item_btn = Button(size_hit_y=None, height=50, color="blue")
        # self.create_food_item_btn.text="Create a food item"
        # self.create_food_item_btn.bind(on_press=self.on_create_food_button)

        options_box = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(120),
            padding=dp(0),
            spacing=dp(0)
        )

        self.grid1 = GridLayout(cols=1, size_hint_y=None, height=dp(120))
        self.grid1.bind(minimum_height=self.grid.setter("height"))
        self.grid1.add_widget(self.chooseFoodBtn)
        self.grid1.add_widget(self.create_new_food_btn)
        options_box.add_widget(self.grid1)

        grid2 = GridLayout(cols=1, size_hint_y=None, height=dp(120))
        grid2.add_widget(self.see_calendar)
        grid2.add_widget(self.clear_food_btn)
        options_box.add_widget(grid2)
        self.add_widget(options_box)
        # Initial population

        foodItems = foodList
        # print(foodItems)
        self.update_buttons(foodItems[:10])

    def update_height(self, *args):
        self.height = max(dp(60), self.clickableLabel.texture_size[1] + dp(20))

    def on_create_food_button(self, instance):
        layout = BoxLayout(orientation="horizontal", spacing=dp(10), padding=dp(10), size_hint_y=None, height=dp(350))

        # label = Label(text="Create new food item")
        # layout.add_widget(label)

        new_food_input = TextInput(hint_text="Food name", multiline=False)
        new_food_cal = TextInput(hint_text="Calories (per 100g)", multiline=False)
        new_food_prot = TextInput(hint_text="Protein (per 100g)", multiline=False)
        new_food_carbs = TextInput(hint_text="Carbohydrates (per 100g)", multiline=False)
        new_food_fat = TextInput(hint_text="Fat (per 100g)", multiline=False)
        new_food_portions = TextInput(hint_text="Portions by weight in grams, delineated with commas \n(e.g.: \"cup: 250, \"tbsp: 15\")", multiline=False)
        
        gridNewFood = GridLayout(cols=1, spacing=dp(10))
        gridNewFood.add_widget(new_food_input)
        gridNewFood.add_widget(new_food_cal)
        gridNewFood.add_widget(new_food_prot)
        gridNewFood.add_widget(new_food_carbs)
        gridNewFood.add_widget(new_food_fat)
        gridNewFood.add_widget(new_food_portions)


        btn = Button(text="Add")
        layout.add_widget(gridNewFood)
        # layout.add_widget(btn)
        
        btnDel = Button(text="Delete")

        btnNo = Button(text="Cancel")
        # layout.add_widget(btnNo)

        gridButtons = GridLayout(cols=1, spacing=dp(10))
        gridButtons.add_widget(btn)
        gridButtons.add_widget(btnDel)
        gridButtons.add_widget(btnNo)
        layout.add_widget(gridButtons)

        popup = Popup(
            title="Create New Food Item",
            content=layout,
            size_hint=(0.7, None),
            height=dp(430),
            auto_dismiss=False
        )

        def on_confirm(instance1):
            new_foodName = new_food_input.text.strip()

            def openErrorPopup(message="Calories/Protein empty"):
                tempBox = BoxLayout(orientation="vertical")
                tempBox.add_widget(Label(text=message))
                tempBox.add_widget(Button(text="Ah Sorry!", size_hint_y=None, height=dp(40), on_press=lambda x: tempPopup.dismiss()))
                tempPopup = Popup(title="Error", content=tempBox, size_hint=(0.6, 0.3))
                tempPopup.open()
                return

            if not new_food_cal.text.strip() or not new_food_prot.text.strip():
                openErrorPopup(message = "Calories/Protein empty")
                return

            try:
                new_foodCal = float(new_food_cal.text.strip())
                new_foodProt = float(new_food_prot.text.strip())
                new_foodCarbs = float(new_food_carbs.text.strip() or 0)
                new_foodFat = float(new_food_fat.text.strip() or 0)
            except:
                openErrorPopup(message= "Macronutrient fields must be a number")

            #portionsList starts with items like "cup: 250"
            portionsList = new_food_portions.text.strip().split(",")
            new_portionsDict = {}
            for item in portionsList:
                if ":" not in item: 
                    openErrorPopup(message="Incorrect format in portions (\"name: weight_grams\") \nExample: (\"cup: 250, oz:28.3\")")
                    return
                name, weight = item.split(":")
                table = str.maketrans({" ":"", "\"":"", "\n":""}) #Remove spaces, new lines
                try:
                    print("name, weight:",name,weight)
                    portionGrams = float(weight.translate(table))
                    print("portionGrams:",portionGrams)
                    print("portionGrams.is_integer():",portionGrams.is_integer())
                    print("int(portionGrams):",int(portionGrams))
                    new_portionsDict[name.translate(table)] = int(portionGrams) if portionGrams.is_integer() else portionGrams
                except:
                    openErrorPopup(message="Incorrect format in portions (\"name: weight_grams\") \nExample: (\"cup: 250, oz:28.3\")")
                    return
                # new_portionsDict[name.strip(" \"\'")] = weight.strip(" \"\'")

            new_foodCal = int(new_foodCal) if new_foodCal.is_integer() else new_foodCal
            new_foodProt = int(new_foodProt) if new_foodProt.is_integer() else new_foodProt
            new_foodCarbs = int(new_foodCarbs) if new_foodCarbs.is_integer() else new_foodCarbs
            new_foodFat = int(new_foodFat) if new_foodFat.is_integer() else new_foodFat

            data = []
            filepath = (get_base())/f"organized_food_data.json"
            if (filepath).exists():
                with open(filepath, "r") as f:
                    data = json.load(f)
                # data[new_foodName] = [new_foodCal, new_foodProt]
                foodEntry = {"name": new_foodName, "protein": new_foodProt, "carbs": new_foodCarbs, "fat": new_foodFat, "cals": new_foodCal, "portions": new_portionsDict}
                data.append(foodEntry)
                with open(filepath, "w") as f:
                    json.dump(data, f)
                # self.update_todays_food()
                self.foodList.append(foodEntry)
                # self.refresh_food_buttons_color()
            popup.dismiss()  # close popup

        def on_del(instance):
            delFood = new_food_input.text.strip()
            data = []
            filepath = (get_base())/f"organized_food_data.json"
            if (filepath).exists():
                with open(filepath, "r") as f:
                    data = json.load(f)
                for foodEntry in data:
                    if foodEntry["name"] == delFood:
                        data.remove(foodEntry)
                        break
                else:
                    tempBox = BoxLayout(orientation="vertical")
                    tempBox.add_widget(Label(text="Food not found!"))
                    tempBox.add_widget(Button(text="OK", size_hint_y=None, height=dp(40), on_press=lambda x: tempPopup.dismiss()))
                    tempPopup = Popup(title="Error", content=tempBox, size_hint=(0.6, 0.3))
                    tempPopup.open()
                    return
                with open(filepath, "w") as f:
                    json.dump(data, f)
                # self.update_todays_food()
                delFoodEntry = next(foodEntry for foodEntry in self.foodList if foodEntry["name"] == delFood)
                self.foodList.remove(delFoodEntry)
                self.selectedFoods.remove(delFoodEntry)
                # self.update_buttons(list(self.foodList.items())[:10])
                self.update_buttons(self.foodList[:10])
                # self.selectedFoods.pop(delFood)
                # self.refresh_food_buttons_color()
            popup.dismiss()  # close popup

        btn.bind(on_press=on_confirm)
        btnDel.bind(on_press=on_del)
        btnNo.bind(on_press=popup.dismiss)
        popup.open()

    def on_textOld(self, instance, value):
        value = value.lower()
        # foodNames = [food["name"] for food in self.foodList]

        # filtered = [
        #     item for item in foodNames
        #     if value in item.lower()
        # ]

        filtered = [
            item for item in self.foodList
            if value in item["name"].lower()
        ]

        filtered = []
        for item in self.foodList:
            #1, tokenize and clean the text with lower, replace("-", " "), split(" "), replace(" ",""), remove punctuation, duplicates, maybe unecessary words like "with"
            foodText = item["name"].lower()
            value = value.replace("-", " ")
            foodText=foodText.replace("-"," ")
            to_remove = string.punctuation #Remove punctuation
            translator = str.maketrans('', '', to_remove)
            value = value.translate(translator) #Search
            foodText = foodText.translate(translator)
            entryStrings = foodText.split(" ")
            searchStrings = value.split(" ")
            #Remove duplicates
            searchStrings = list(set(searchStrings))
            entryStrings = list(set(entryStrings))
            
            #2, Match the most similar tokens in search to the tokens in entry with the Levenshtein score, penalize scores under 0.6 (60%), average, and penalize 0.05 from the number of unmatched entry tokens
            
            #Let's make a dict with keys of searchStrings, with values being a dict for each with keys of each entryStrings and values of similarity. e.g. {s1:{e1:0.5, e2:0.2}, s2:{e1:0.2, e2 0.6}}
            similarityDict = {}
            similarityThreshold = 0.6
            for searchString in searchStrings:
                # usedEntries = set()
                similarityDict[searchString] = []

                for entryString in entryStrings:
                    # if entryString in usedEntries: continue
                    # similarity = Levenshtein.ratio(searchString, entryString)
                    #Lehvenstein ratio formula is (n+m-dist)/(n+m)
                    n,m=len(searchString),len(entryString)
                    similarity = (n+m-Levenshtein.distance(searchString, entryString))/(n+m)
                    if similarity < similarityThreshold: similarity *= 0.6
                    similarityDict[searchString].append((entryString, similarity))

                    # usedEntries.add(entryString)

            #Now let's pick out the highest similarity values one by one and match each token
            matchesDict = {}
            best_matches = {}
            usedEntries = set()
            usedSearch = set()
            # sortedSimDict =  {s: dict(sorted(similarity, key=lambda x: x[1], reverse=True)) 
            #                  for entry, similarity in similarityDict.items()}
            similarityDict[searchString].sort(key=lambda x: x[1], reverse=True)
            
            #We can fix our stuff later, this is still just a greedy search for the best matches by similarity, not optimal
            for k, v in similarityDict.items():
                #When we think of the dict, it basically creates a matrix where each search key has the same number of items
                # we have to find the entries with key with the highest similarity, and that one will be chosen
                highestEntryMatches = {} # k:(entry,similarity)
                for entry, similarity in v:
                    highestMatch = highestEntryMatches.get(k)
                    if similarity > highestMatch[k][1]: 
                        highestMatch[k] = (entry, similarity)
                
            # for k in sortedSimDict.keys():
            #     bestE, bestSim = None,0
            #     if bestE in usedEntries: continue
            #     entrySim = sortedSimDict[k]
            #     for e, sim in entrySim.items():
            #         if sim > bestSim:
            #             bestSim = sim
            #             bestE = e
            #     best_matches[k] = bestE
            #     usedEntries.add(bestE)
            #     usedSearch.add(k)



        self.update_buttons(filtered[:10])

    def on_text1(self, instance, value):
        value = value.lower()
        value = "commercial hummus".lower()


        filtered = [
            item for item in self.foodList
            if value in item["name"].lower()
        ]
        used_entry = set()

        filtered = []
        for item in self.foodList:
            #region tokenize
            #1, tokenize and clean the text with lower, replace("-", " "), split(" "), replace(" ",""), remove punctuation, duplicates, maybe unecessary words like "with"
            foodText = item["name"].lower()
            value = value.replace("-", " ")
            foodText=foodText.replace("-"," ")
            to_remove = string.punctuation #Remove punctuation
            translator = str.maketrans('', '', to_remove)
            value = value.translate(translator) #Search
            foodText = foodText.translate(translator)
            entryStrings = foodText.split(" ")
            searchStrings = value.split(" ")
            #Remove duplicates
            searchStrings = list(set(searchStrings))
            entryStrings = list(set(entryStrings))
            #endregion
            
            #2, Match the most similar tokens in search to the tokens in entry with the Levenshtein score, penalize scores under 0.6 (60%), average, and penalize 0.05 from the number of unmatched entry tokens
            
            #Let's make a dict with keys of searchStrings, with values being a dict for each with keys of each entryStrings and values of similarity. e.g. {s1:{e1:0.5, e2:0.2}, s2:{e1:0.2, e2 0.6}}
            similarityDict = {}
            similarityThreshold = 0.6
            for searchString in searchStrings:
                # usedEntries = set()
                similarityDict[searchString] = []

                for entryString in entryStrings:
                    # if entryString in usedEntries: continue
                    # similarity = Levenshtein.ratio(searchString, entryString)
                    n,m=len(searchString),len(entryString)
                    similarity = (n+m-Levenshtein.distance(searchString, entryString))/(n+m)
                    if similarity < similarityThreshold: similarity *= 0.6
                    similarityDict[searchString].append((entryString, similarity))

                    # usedEntries.add(entryString)
                similarityDict[searchString].sort(key=lambda x: x[1], reverse=True)

            #This should make the whole greedy algorithm on the matching 
            pairs = []

            for k, v in similarityDict.items():
                for entry, sim in v:
                    pairs.append((sim, k, entry))

                pairs.sort(reverse=True)

                used_k = set()
                # used_entry = set()
                matches = {}

                for sim, k, entry in pairs:
                    if k in used_k or entry in used_entry:
                        continue

                    matches[k] = (entry, sim)
                    used_k.add(k)
                    used_entry.add(entry)
            
                filtered.append(matches)
            #Similarity scores have been applied to each search token, and now we need to minus the number of unmatched entry tokens

        print("matches:",filtered)

        filtered = list(used_entry)


        # self.update_buttons(filtered[:10])

    def on_text(self, instance, value):
        filtered = []

        value_clean = value.lower()
        value_clean = value_clean.replace("-", " ")

        translator = str.maketrans('', '', string.punctuation)
        value_clean = value_clean.translate(translator)

        search_tokens = value_clean.split()

        if not search_tokens:
            print("matches: []")
            return

        entry_sim_dict = {}

        # for item in self.foodList:
        for foodText, entry_tokens in self.foodEntryTokens.items():
            # foodText = item["name"].lower()
            # foodText = foodText.replace("-", " ")
            # foodText = foodText.translate(translator)

            if not set(search_tokens) & set(entry_tokens): 
                # fallback: allow fuzzy candidates
                if not any(s[:3] in e or e[:3] in s for s in search_tokens for e in entry_tokens):
                    continue

            if not entry_tokens:
                continue

            similarity_vector = []

            for s in search_tokens:
                best_sim = 0

                for e in entry_tokens:
                    # sim = Levenshtein.ratio(s, e)
                    n,m=len(s),len(e)
                    sim = (n+m-Levenshtein.distance(s, e))/(n+m)

                    if sim < 0.6:
                        sim *= 0.6

                    best_sim = max(best_sim, sim)
                    if best_sim == 1.0:
                        break

                similarity_vector.append(best_sim)

            avg_score = sum(similarity_vector) / len(similarity_vector)

            missing_penalty = max(0, len(search_tokens) - len(entry_tokens)) * 0.05

            adjusted_score = avg_score - missing_penalty

            # entry_sim_dict[item["name"]] = adjusted_score
            # entry_sim_dict[foodText] = adjusted_score

            # filtered.append((adjusted_score, item))
            filtered.append((adjusted_score, self.foodDict[foodText]))

        filtered = sorted(filtered, key=lambda x: x[0], reverse=True)[:10]
        filtered1 = []
        for d in filtered:
            # if d[0] > 0.5:
            filtered1.append(d[1])


        # print("matches:", filtered1)
        self.update_buttons(filtered1)
#hummus comm
    def update_buttons(self, items): #Items will be a sliced list from food.json with dicts like 
        # {"name": "foodName", "protein": 0, "carbs": 0, "fat": 0, "cals": 0, "portions": {"portionName": weightInGrams}}

        for i in range(10):
            if i < len(items):
                foodEntry = items[i]
                self.buttons[i].text = foodEntry["name"]
                self.buttons[i].disabled = False
                self.buttons[i].foodValue = foodEntry
                self.update_food_buttons_color(self.buttons[i])
            else:
                self.buttons[i].text = ""
                self.buttons[i].disabled = True
                self.buttons[i].foodValue = None
                self.buttons[i].background_color = (1,1,1,1)
                self.update_food_buttons_color(self.buttons[i])

    def refresh_food_buttons_color(self):
        for btn in self.buttons:
            self.update_food_buttons_color(btn)

    def update_food_buttons_color(self, instance): #instance variables can be found in update_buttons        
        # if instance.text not in self.selectedFoods:
        if any(instance.text == d["name"] for d in self.selectedFoods):
            instance.background_color="red"
        else:
            instance.background_color=(1,1,1,1)

    def on_food_button_press(self, instance): #instance variables can be found in update_buttons        
        # if instance.text not in self.selectedFoods:
        
        matchingFoodEntry = next((d for d in self.selectedFoods if instance.text == d["name"]), None)
        
        # if any(instance.text == d["name"] for d in self.selectedFoods):
        if matchingFoodEntry:
            self.selectedFoods.remove(matchingFoodEntry)
            instance.background_color=(1,1,1,1)
        else:
            self.selectedFoods.append(instance.foodValue)
            instance.background_color="red"
        # print(self.selectedFoods)

        # print("Selected:", instance.text)
        # return instance.text

    def on_choose_food_button_press(self, instance):
        app = App.get_running_app()
        detail_screen = app.root.get_screen("detail")
        detail_screen.update_todays_food()
        # detail_screen.update_select_food_grid()

        print("Adding "+str(self.selectedFoods))
        detail_screen.food_list.clear_widgets()
        detail_screen.update_select_food_grid()
        # for foodName, v in list(self.selectedFoods.items()):
        #     detail_screen.add_food_widget_number(foodName, v[0], v[1])
        detail_screen.food_list.add_widget(Widget())
        foodNames = [foodEntry["name"] for foodEntry in self.selectedFoods]
        detail_screen.label.text = str(foodNames)[1:-1].replace("'","")

        # detail_screen.add_widget()

        app.root.current = "detail"

    def on_add_food_numbers(self, instance):
        app = App.get_running_app()
        detail_screen = app.root.get_screen("detail")

        pass

    def on_see_calendar(self, instance):
        app = App.get_running_app()
        app.root.current = "calendar"
    


class MyApp(App):
    def build(self):
        sm = ScreenManager()

        # Load JSON
        food_path = get_base() / "organized_food_data.json"
        if not food_path.exists():
            source = resource_find("MealLogs/organized_food_data.json")
            shutil.copy(source, food_path)

        with open(food_path, "r") as f:
            self.foodList = json.load(f)
        print("food size dict:", len(self.foodList))
        # if not (get_base()/"organized_food_data.json").exists():
        #     with open("organized_food_data.json", "r") as f:
        #         fd = json.load(f)
        #         with open(get_base()/"organized_food_data.json", "w") as f:
        #             json.dump(fd, f, indent=4)
                # json.dump({"meat (100g)": [240, 25], "cheese slice": [80, 4.5], "ham slice": [50, 3.5], "egg (L)": [70, 6.3], "veg (S)": [45, 0], "butter (tbsp)": [100, 0], "oil (tbsp)": [120, 0], "fat (tbsp)": [120, 0], "banana (M)": [105, 1.3], "apple (M)": [85, 0.5], "orange (M)": [62, 1.2], "bread slice": [75, 3], "rice (100g)": [130, 2.7], "boiled pasta (100g)": [140, 5], "milk (2%, cup)": [120, 8], "yogurt (cup)": [150, 10], "greek yogurt (2%, cup)": [150, 19], "chicken broth (1 cup)": [25, 3], "beef broth (1 cup)": [30, 2], "vegetable broth (1 cup)": [10, 0.5], "cereal (cup)": [155, 4], "oatmeal (cooked, cup)": [155, 5], "granola (cup)": [250, 7.5], "peanut butter (tbsp)": [90, 4], "almond butter (tbsp)": [98, 3.3], "honey (tbsp)": [64, 0.1], "jam (tbsp)": [50, 0.1], "butter (g)": [7.2, 0.01], "oil (g)": [8.9, 0], "fat (g)": [9, 0], "avocado (M)": [240, 3], "nuts (100g)": [600, 18], "seeds (100g)": [580, 22.5], "fruit juice (cup)": [115, 1], "soda (can)": [150, 0], "coffee (cup)": [3.5, 0.3], "tea (cup)": [2, 0.1]}, f, indent=4)
        # # with open(get_base()/"organized_food_data.json", "r") as f:
        # #     self.foodList = json.load(f)
            # print(self.foodList)
        # return

        # self.keys = list(self.foodList.keys())
        self.foodItems = self.foodList
        self.selectedFoods = []
        self.todaysFoods = {} #Will be like {"Meal1": {"foodQuantities": [[foodList, qty], [foodList, qty]], calories, protein } }
        if (get_base()/f"MealLog_{datetime.date.today()}.json").exists():
            with open(get_base()/f"MealLog_{datetime.date.today()}.json", "r") as f:
                self.todaysFoods = json.load(f)
        sm.add_widget(SearchScreen(name="search"))
        sm.add_widget(DetailScreen(name="detail"))
        sm.add_widget(CalendarScreen(name="calendar"))


        return sm

#Helper functions
def normalize_meals_dict(data):
    def get_num(k):
        return int(k.replace("Meal", ""))

    items = []
    total_cal = 0
    total_prot = 0
    total_carbs = 0
    total_fat = 0

    for k, v in data.items():
        if k == "<Total>":
            continue
        items.append((get_num(k), v))
        total_cal += v["calories"]
        total_prot += v["protein"]
        total_carbs += v["carbs"]
        total_fat += v["fat"]

    items.sort(key=lambda x: x[0])

    new_data = {}
    for i, (_, value) in enumerate(items, 1):
        new_data[f"Meal{i}"] = value

    new_data["<Total>"] = {"calories": total_cal, "protein": total_prot, "carbs": total_carbs, "fat": total_fat}
    return new_data

class ClickableLabel(ButtonBehavior, Label):
    pass


if __name__ == "__main__":
    # os.makedirs("MealLogs", exist_ok=True)
    get_base().mkdir(parents=True, exist_ok=True)
    MyApp().run()