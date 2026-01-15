# Kivy Mobile App

Prosta aplikacja mobilna (Android/iOS) – kalkulator BMI.

## Uruchomienie

```bash
markpact examples/kivy-mobile/README.md
```

Aplikacja otworzy się w oknie desktopowym. Aby zbudować APK:

```bash
cd sandbox
pip install buildozer
buildozer android debug
```

## Funkcje

- Kalkulator BMI
- Interpretacja wyniku
- Historia obliczeń
- Material Design UI

---

```text markpact:deps python
kivy
```

```python markpact:file path=main.py
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.core.window import Window
from kivy.utils import get_color_from_hex

# Mobile-friendly window size
Window.size = (360, 640)

class BMICalculator(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = 20
        self.spacing = 15
        self.history = []
        
        # Title
        self.add_widget(Label(
            text='[b]BMI Calculator[/b]',
            markup=True,
            font_size='24sp',
            size_hint_y=None,
            height=50,
            color=get_color_from_hex('#2196F3')
        ))
        
        # Weight input
        self.add_widget(Label(text='Weight (kg):', size_hint_y=None, height=30))
        self.weight_input = TextInput(
            hint_text='Enter weight...',
            input_filter='float',
            multiline=False,
            size_hint_y=None,
            height=50,
            font_size='18sp'
        )
        self.add_widget(self.weight_input)
        
        # Height input
        self.add_widget(Label(text='Height (cm):', size_hint_y=None, height=30))
        self.height_input = TextInput(
            hint_text='Enter height...',
            input_filter='float',
            multiline=False,
            size_hint_y=None,
            height=50,
            font_size='18sp'
        )
        self.add_widget(self.height_input)
        
        # Calculate button
        calc_btn = Button(
            text='Calculate BMI',
            size_hint_y=None,
            height=60,
            background_color=get_color_from_hex('#4CAF50'),
            font_size='18sp'
        )
        calc_btn.bind(on_press=self.calculate_bmi)
        self.add_widget(calc_btn)
        
        # Result label
        self.result_label = Label(
            text='Enter your data above',
            font_size='20sp',
            size_hint_y=None,
            height=80
        )
        self.add_widget(self.result_label)
        
        # History section
        self.add_widget(Label(
            text='[b]History[/b]',
            markup=True,
            size_hint_y=None,
            height=30
        ))
        
        self.history_scroll = ScrollView(size_hint=(1, 1))
        self.history_layout = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            spacing=5
        )
        self.history_layout.bind(minimum_height=self.history_layout.setter('height'))
        self.history_scroll.add_widget(self.history_layout)
        self.add_widget(self.history_scroll)
    
    def calculate_bmi(self, instance):
        try:
            weight = float(self.weight_input.text)
            height_cm = float(self.height_input.text)
            height_m = height_cm / 100
            
            bmi = weight / (height_m ** 2)
            
            # Interpretation
            if bmi < 18.5:
                category = "Underweight"
                color = "#FFC107"
            elif bmi < 25:
                category = "Normal"
                color = "#4CAF50"
            elif bmi < 30:
                category = "Overweight"
                color = "#FF9800"
            else:
                category = "Obese"
                color = "#F44336"
            
            result = f"BMI: {bmi:.1f} ({category})"
            self.result_label.text = result
            self.result_label.color = get_color_from_hex(color)
            
            # Add to history
            history_item = Label(
                text=f"{weight}kg, {height_cm}cm → {bmi:.1f}",
                size_hint_y=None,
                height=30,
                font_size='14sp'
            )
            self.history_layout.add_widget(history_item)
            
        except ValueError:
            self.result_label.text = "Please enter valid numbers"
            self.result_label.color = get_color_from_hex('#F44336')

class BMIApp(App):
    def build(self):
        return BMICalculator()

if __name__ == '__main__':
    BMIApp().run()
```

```ini markpact:file path=buildozer.spec
[app]
title = BMI Calculator
package.name = bmicalc
package.domain = org.markpact
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 1.0.0
requirements = python3,kivy
orientation = portrait
fullscreen = 0
android.permissions = INTERNET
android.api = 31
android.minapi = 21
android.arch = arm64-v8a

[buildozer]
log_level = 2
warn_on_root = 1
```

```bash markpact:run
python main.py
```
