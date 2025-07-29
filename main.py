# main.py
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelItem
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.dropdown import DropDown
from kivy.uix.spinner import Spinner
import json
import os
from datetime import datetime, date
from collections import defaultdict
import calendar

class BudgetManager:
    def __init__(self, data_file='budget_data.json'):
        self.data_file = data_file
        self.data = self.load_data()
        self.update_balance_for_current_date()
    
    def load_data(self):
        if os.path.exists(self.data_file):
            with open(self.data_file, 'r') as f:
                data = json.load(f)
                # Убедимся, что все необходимые поля существуют
                required_fields = ['daily_budget', 'current_balance', 'transactions', 'last_date', 'last_balance']
                for field in required_fields:
                    if field not in data:
                        if field == 'daily_budget':
                            data[field] = 0
                        elif field == 'current_balance':
                            data[field] = 0
                        elif field == 'transactions':
                            data[field] = []
                        elif field == 'last_date':
                            data[field] = str(date.today())
                        elif field == 'last_balance':
                            data[field] = 0
                return data
        return {
            'daily_budget': 0,
            'current_balance': 0,
            'transactions': [],
            'last_date': str(date.today()),
            'last_balance': 0
        }
    
    def save_data(self):
        with open(self.data_file, 'w') as f:
            json.dump(self.data, f, indent=2)
    
    def update_balance_for_current_date(self):
        """Обновляем баланс с учетом пропущенных дней"""
        today = str(date.today())
        last_date = self.data['last_date']
        
        if last_date != today:
            # Рассчитываем количество пропущенных дней
            last_date_obj = datetime.strptime(last_date, '%Y-%m-%d').date()
            today_obj = datetime.strptime(today, '%Y-%m-%d').date()
            days_passed = (today_obj - last_date_obj).days
            
            # Добавляем ежедневный бюджет за каждый пропущенный день + остаток
            if days_passed > 0:
                additional_budget = self.data['daily_budget'] * days_passed
                self.data['current_balance'] += additional_budget
            
            self.data['last_date'] = today
            self.save_data()
    
    def set_daily_budget(self, amount):
        old_budget = self.data['daily_budget']
        self.data['daily_budget'] = amount
        today = str(date.today())
    
        if self.data['last_date'] != today:
            # Если новая дата, обновляем баланс
            self.update_balance_for_current_date()
            # Добавляем сегодняшний бюджет
            self.data['current_balance'] += amount
        else:
            # Если та же дата, пересчитываем разницу
            if old_budget != 0:
                # Вычисляем разницу между новым и старым бюджетом
                difference = amount - old_budget
                # Добавляем разницу к текущему балансу
                self.data['current_balance'] += difference
            else:
                # Если первый ввод бюджета за день
                if self.data['current_balance'] == 0 and len(self.data['transactions']) == 0:
                    self.data['current_balance'] = amount
    
        self.data['last_balance'] = self.data['current_balance']
        self.save_data()
    
    def add_expense(self, amount, description=""):
        # Разрешаем отрицательный баланс
        self.data['current_balance'] -= amount
        transaction = {
            'date': str(datetime.now()),  # Точное время с устройства
            'amount': amount,
            'description': description,
            'type': 'expense'
        }
        self.data['transactions'].append(transaction)
        self.save_data()
        return True
    
    def get_balance(self):
        return self.data['current_balance']
    
    def get_daily_budget(self):
        return self.data['daily_budget']
    
    def get_transactions(self):
        return self.data['transactions']
    
    def get_transactions_by_date(self):
        """Группируем транзакции по датам"""
        transactions_by_date = defaultdict(list)
        for transaction in self.data['transactions']:
            # Извлекаем дату из datetime
            trans_date = transaction['date'].split(' ')[0]
            transactions_by_date[trans_date].append(transaction)
        return dict(transactions_by_date)
    
    def get_daily_summary(self):
        """Получаем сводку по дням с итогами"""
        transactions_by_date = self.get_transactions_by_date()
        summary = {}
        
        for trans_date, transactions in transactions_by_date.items():
            total_expense = sum(t['amount'] for t in transactions)
            summary[trans_date] = {
                'transactions': transactions,
                'total_expense': total_expense
            }
        return summary
    
    def format_date_russian(self, date_str):
        """Форматируем дату в русском стиле: 2 Марта 2025"""
        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
            months = [
                'Января', 'Февраля', 'Марта', 'Апреля', 'Мая', 'Июня',
                'Июля', 'Августа', 'Сентября', 'Октября', 'Ноября', 'Декабря'
            ]
            month_name = months[date_obj.month - 1]
            return f"{date_obj.day} {month_name} {date_obj.year}"
        except:
            return date_str

class MainTab(BoxLayout):
    def __init__(self, budget_manager, history_tab=None, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.budget_manager = budget_manager
        self.history_tab = history_tab
        
        # Заголовок
        self.add_widget(Label(text='Бюджетный трекер', size_hint_y=0.1))
        
        # Отображение баланса
        self.balance_label = Label(text='Баланс: 0 руб', font_size=18)
        self.add_widget(self.balance_label)
        
        # Ввод дневного бюджета
        budget_layout = BoxLayout(size_hint_y=0.15)
        budget_layout.add_widget(Label(text='Дневной бюджет:'))
        self.budget_input = TextInput(multiline=False, input_filter='float')
        budget_layout.add_widget(self.budget_input)
        set_budget_btn = Button(text='Установить', size_hint_x=0.3)
        set_budget_btn.bind(on_press=self.set_budget)
        budget_layout.add_widget(set_budget_btn)
        self.add_widget(budget_layout)
        
        # Ввод расхода
        expense_layout = BoxLayout(size_hint_y=0.15)
        expense_layout.add_widget(Label(text='Расход:'))
        self.expense_input = TextInput(multiline=False, input_filter='float')
        expense_layout.add_widget(self.expense_input)
        self.description_input = TextInput(multiline=False, hint_text='Описание')
        expense_layout.add_widget(self.description_input)
        add_expense_btn = Button(text='Добавить', size_hint_x=0.3)
        add_expense_btn.bind(on_press=self.add_expense)
        expense_layout.add_widget(add_expense_btn)
        self.add_widget(expense_layout)
        
        # Кнопка обновления
        refresh_btn = Button(text='Обновить', size_hint_y=0.1)
        refresh_btn.bind(on_press=self.update_display)
        self.add_widget(refresh_btn)
        
        # Обновляем отображение
        self.update_display()
    
    def set_history_tab(self, history_tab):
        """Установка ссылки на вкладку истории"""
        self.history_tab = history_tab
    
    def set_budget(self, instance):
        try:
            amount = float(self.budget_input.text)
            old_budget = self.budget_manager.get_daily_budget()
            
            # Устанавливаем новый бюджет
            self.budget_manager.set_daily_budget(amount)
            
            # Обновляем отображение
            self.update_display()
            self.budget_input.text = ''
            
            # Обновляем историю если она существует
            if self.history_tab:
                self.history_tab.update_history()
                
        except ValueError:
            pass
    
    def add_expense(self, instance):
        try:
            amount = float(self.expense_input.text)
            description = self.description_input.text
            if amount > 0:
                self.budget_manager.add_expense(amount, description)
                self.update_display()
                self.expense_input.text = ''
                self.description_input.text = ''
                # Обновляем историю если она существует
                if self.history_tab:
                    self.history_tab.update_history()
        except ValueError:
            pass
    
    def update_display(self, instance=None):
        balance = self.budget_manager.get_balance()
        daily_budget = self.budget_manager.get_daily_budget()
        self.balance_label.text = f'Баланс: {balance:.2f} руб\nЕжедневный бюджет: {daily_budget:.2f} руб'

class FilterWidget(BoxLayout):
    def __init__(self, on_filter_change, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.size_hint_y = None
        self.height = 60
        self.padding = [10, 10, 10, 10]
        self.spacing = 10
        self.on_filter_change = on_filter_change
        
        label = Label(
            text='Фильтр:', 
            size_hint_x=None, 
            width=60,
            color=(1, 1, 1, 1)
        )
        self.add_widget(label)
        
        self.filter_input = TextInput(
            multiline=False, 
            size_hint_x=0.7,
            background_color=(1, 1, 1, 1),
            foreground_color=(0, 0, 0, 1),
            hint_text='Введите дату или описание...',
            hint_text_color=(0.5, 0.5, 0.5, 1),
            padding=[10, 10, 10, 10],
            font_size=16
        )
        self.filter_input.bind(text=self.on_text_change)
        self.add_widget(self.filter_input)
        
        clear_btn = Button(
            text='Сброс', 
            size_hint_x=0.3,
            background_color=(0.3, 0.3, 0.3, 1),
            color=(1, 1, 1, 1)
        )
        clear_btn.bind(on_press=self.clear_filter)
        self.add_widget(clear_btn)
        
        self.filter_input.focus = True
    
    def on_text_change(self, instance, value):
        self.on_filter_change(value)
    
    def clear_filter(self, instance):
        self.filter_input.text = ''
        self.filter_input.focus = True
        self.on_filter_change('')

class HistoryTab(ScrollView):
    def __init__(self, budget_manager, **kwargs):
        super().__init__(**kwargs)
        self.budget_manager = budget_manager
        self.current_filter = ''
        self.grid_layout = GridLayout(cols=1, size_hint_y=None, spacing=10, padding=10)
        self.grid_layout.bind(minimum_height=self.grid_layout.setter('height'))
        self.add_widget(self.grid_layout)
        
        # Создаем фильтр один раз
        self.filter_widget = FilterWidget(self.set_filter)
        self.grid_layout.add_widget(self.filter_widget)
        
        self.update_history()

    def set_filter(self, filter_text):
        self.current_filter = filter_text.strip()
        # Обновляем только историю, не пересоздаем фильтр
        self.update_history_only()

    def update_history(self):
        # Полное обновление (при первом запуске)
        self.update_history_only()

    def update_history_only(self):
        # Очищаем все, кроме фильтра
        widgets_to_remove = []
        for widget in self.grid_layout.children:
            if widget != self.filter_widget:
                widgets_to_remove.append(widget)
        
        for widget in widgets_to_remove:
            self.grid_layout.remove_widget(widget)

        transactions_by_date = self.budget_manager.get_transactions_by_date()
        sorted_dates = sorted(transactions_by_date.keys(), reverse=True)

        # Если есть фильтр, показываем его в заголовке
        if self.current_filter:
            filter_info = Label(
                text=f'Фильтр: "{self.current_filter}"',
                size_hint_y=None,
                height=30,
                color=(0.8, 0.8, 1, 1)
            )
            self.grid_layout.add_widget(filter_info)

        for trans_date in sorted_dates:
            transactions = transactions_by_date[trans_date]
            filtered_transactions = transactions
            
            if self.current_filter:
                filter_lower = self.current_filter.lower()
                formatted_date = self.budget_manager.format_date_russian(trans_date).lower()
                original_date = trans_date.lower()
                
                # Проверяем совпадение по дате
                date_match = (filter_lower in original_date or filter_lower in formatted_date)
                
                if date_match:
                    filtered_transactions = transactions
                else:
                    filtered_transactions = [
                        t for t in transactions 
                        if filter_lower in t['description'].lower()
                    ]
                
                if not filtered_transactions and not date_match:
                    continue

            # Создаем блок для дня (как раньше)
            day_box = BoxLayout(orientation='vertical', size_hint_y=None)
            
            formatted_date = self.budget_manager.format_date_russian(trans_date)
            total_expense = sum(t['amount'] for t in filtered_transactions)

            header_text = f'{formatted_date}'
            day_header = Label(
                text=header_text,
                bold=True,
                size_hint_y=None,
                height=45,
                halign='center',
                valign='middle',
                color=(1, 1, 1, 1),
                font_size=18
            )
            day_box.add_widget(day_header)

            for transaction in filtered_transactions:
                try:
                    trans_time = datetime.strptime(transaction['date'], '%Y-%m-%d %H:%M:%S.%f').strftime('%H:%M')
                except:
                    trans_time = ''

                trans_text = f"  {trans_time}   -{transaction['amount']:.2f} руб   {transaction['description']}  "
                trans_label = Label(
                    text=trans_text,
                    size_hint_y=None,
                    height=40,
                    halign='left',
                    valign='middle',
                    text_size=(self.width + 30, None),
                    color=(1, 1, 1, 1),
                    font_size=14
                )
                trans_label.bind(texture_size=trans_label.setter('size'))
                day_box.add_widget(trans_label)

            total_label = Label(
                text=f'Итог: -{total_expense:.2f} руб',
                bold=True,
                size_hint_y=None,
                height=45,
                halign='center',
                valign='middle',
                color=(1, 0.8, 0.8, 1),
                font_size=16
            )
            day_box.add_widget(total_label)

            separator = Label(
                text='═' * 40,
                size_hint_y=None,
                height=30,
                halign='center',
                color=(0.7, 0.7, 0.7, 1),
                font_size=12
            )
            day_box.add_widget(separator)

            day_box.height = 45 + len(filtered_transactions) * 40 + 45 + 30
            self.grid_layout.add_widget(day_box)

class BudgetApp(App):
    def build(self):
        self.budget_manager = BudgetManager()
        
        # Создаем вкладки
        tab_panel = TabbedPanel(do_default_tab=False)
        
        # Создаем вкладки
        main_tab = MainTab(self.budget_manager)
        history_tab = HistoryTab(self.budget_manager)
        
        # Связываем вкладки
        main_tab.set_history_tab(history_tab)
        
        # Добавляем вкладки
        tab_panel.add_widget(TabbedPanelItem(text='Главная', content=main_tab))
        tab_panel.add_widget(TabbedPanelItem(text='История', content=history_tab))
        
        return tab_panel

if __name__ == '__main__':
    BudgetApp().run()