#!/usr/bin/env python
# coding: utf-8

# In[1]:


#!pip install pywebview


# In[2]:


#библиотеки
from IPython.display import HTML
import folium
import pandas as pd
import ast
import json
import re
import tkinter as tk
import webview


# In[3]:


#Датафрейм с координатами и инфой о домиках:
pd.set_option('display.max_columns', None)
df = pd.read_csv(r'C:\Users\kamar\Desktop\location_p\ml_with_address.csv')

#Удаляем строки где есть пропуски в ЦТП и данных координат:
df = df.dropna(subset=['ЦТП','geoData'])
df.head(3)


# In[4]:


# Функция для редактирования столбца geoData:
def extract_coordinates(row):
    # Паттерн для поиска координат в строке
    pattern = r'\[(\d+\.\d+),\s*(\d+\.\d+)\]'
    # Ищем все вхождения паттерна в строке
    matches = re.findall(pattern, row)
    # Преобразуем в список координат
    coordinates = [[float(match[1]), float(match[0])] for match in matches]
    return coordinates

# В цикле меняем строку geodata_center:
for i in range(len(df['geodata_center'])):    
    df['geodata_center'].values[i] = df['geodata_center'].values[i].replace(
        'coordinates=','"coords":').replace('type=', '"name":').replace('Point', '"Name_polygon"')
    
# Функция для редактирования столбца geodata_center:
def swap_coordinates(coord_string):
    
    # Преобразование строки в словарь
    coord_dict = json.loads(coord_string)
    
    # Поменять местами координаты
    coord_dict['coords'] = [coord_dict['coords'][1], coord_dict['coords'][0]]
    
    return coord_dict

# Применяем функции к сериям:
df['geoData'] = df['geoData'].apply(extract_coordinates)
df['geodata_center'] = df['geodata_center'].apply(swap_coordinates)

# Функция для добавления меток адресов и ЦТП в словарь с координатами:
def update_geodata(row):
    ctp_value = row['ЦТП']
    address_value = row['Адрес']
    geodata = row['geodata_center']
    geodata['name'] = f'Название ЦТП: {ctp_value}, Адрес: {address_value}'
    return geodata

# Применение функции ко всему столбцу 'geodata_center'
df['geodata_center'] = df.apply(update_geodata, axis=1)


# In[5]:


#Фрейм признаков:
df_targets = df[['Температура в квартире ниже нормативной', 'T1 > max', 
                 'Отсутствие отопления в доме', 'Сильная течь в системе отопления', 
                 'Течь в системе отопления', 'geoData', 'geodata_center']]

#Формируем столбец всех критических признаков по предсказаниям модели:
slices = [
    df_targets[df_targets["T1 > max"] > 0.9]['geodata_center'],
    df_targets[df_targets["Температура в квартире ниже нормативной"] > 0.995]['geodata_center'],
    df_targets[df_targets["Отсутствие отопления в доме"] > 0.5]['geodata_center'],
    df_targets[df_targets["Сильная течь в системе отопления"] > 0.5]['geodata_center'],
    df_targets[df_targets["Течь в системе отопления"] > 0.5]['geodata_center']
]

#Метки всех аварий ВАО:
df_emergency = pd.concat(slices).drop_duplicates().reset_index(drop=True)

#Метки всех не аварий ВАО:
df_geodata_center = df['geodata_center'][~df['geodata_center'].isin(df_emergency)]


# In[10]:


# Все метки и полигоны ВАО:
marks_coords = df_geodata_center.tolist()[:1000]
polygons_coords = df['geoData'].tolist()[:1900]
emergency_marks_coords = df_emergency.tolist()

# Критические здания по предсказанию модели для различных целевых:
low_temp_polygons_coords = df_targets[df_targets["Температура в квартире ниже нормативной"] > 0.995]['geoData'].tolist()
hight_temp_polygons_coords = df_targets[df_targets["T1 > max"] > 0.9]['geoData'].tolist()
no_heating_polygons_coords = df_targets[df_targets["Отсутствие отопления в доме"] > 0.5]['geoData'].tolist()
strong_leak_polygons_coords = df_targets[df_targets["Сильная течь в системе отопления"] > 0.5]['geoData'].tolist()
leak_polygons_coords = df_targets[df_targets["Течь в системе отопления"] > 0.5]['geoData'].tolist()

# Преобразование данных в JSON
marks_json = json.dumps(marks_coords)
polygons_json = json.dumps(polygons_coords)
emergency_marks_json = json.dumps(emergency_marks_coords)
low_temp_polygons_json = json.dumps(low_temp_polygons_coords)
hight_temp_polygons_json = json.dumps(hight_temp_polygons_coords)
no_heating_polygons_json = json.dumps(no_heating_polygons_coords)
strong_leak_polygons_json = json.dumps(strong_leak_polygons_coords)
leak_polygons_json = json.dumps(leak_polygons_coords)

# HTML код карты с наложением меток и полигонов:
map_html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Yandex Map</title>
    <script src="https://api-maps.yandex.ru/2.1/?lang=ru_RU" type="text/javascript"></script>
    <style>
        body {{
            font-family: 'Roboto', Arial, sans-serif;
            margin: 0;
            padding: 0;
            user-select: none;
            background-color: #f0f0f0;
        }}
        #map {{
            width: 100%;
            height: 80vh;
            border-bottom: 2px solid #4CAF50;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }}
        .controls {{
            text-align: center;
            margin-top: 10px;
            background-color: #f9f9f9;
            padding: 10px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            display: flex;
            justify-content: center;
            align-items: center;
        }}
        .controls select, .controls button {{
            padding: 10px 20px;
            font-size: 16px;
            margin: 5px;
            cursor: pointer;
            border-radius: 5px;
            border: none;
            transition: all 0.3s ease;
        }}
        .controls button {{
            background-color: #4CAF50;
            color: white;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }}
        .controls button:hover {{
            background-color: #45a049;
            transform: translateY(-2px);
        }}
        .controls select {{
            border: 1px solid #ccc;
            background-color: white;
        }}
        .controls input[type="file"] {{
            display: none;
        }}
        .controls label {{
            padding: 10px 20px;
            font-size: 16px;
            margin: 5px;
            cursor: pointer;
            border-radius: 5px;
            background-color: #4CAF50;
            color: white;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            transition: all 0.3s ease;
        }}
        .controls label:hover {{
            background-color: #45a049;
            transform: translateY(-2px);
        }}
        .settings {{
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            display: none;
            padding: 20px;
            background-color: #ffffff;
            border-radius: 10px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            z-index: 1000;
            transition: opacity 0.3s, transform 0.3s;
            border: 2px solid #4CAF50;
        }}
        .settings.show {{
            display: block;
            opacity: 1;
        }}
        .settings.hide {{
            opacity: 0;
            transform: translate(-50%, -60%);
        }}
        .settings h3 {{
            margin-top: 0;
            cursor: move;
            color: #4CAF50;
        }}
        .settings label {{
            display: block;
            margin-bottom: 10px;
            color: #333;
        }}
        .settings button {{
            margin-top: 10px;
            padding: 10px 20px;
            font-size: 16px;
            border: 2px solid #4CAF50;
            border-radius: 5px;
            cursor: pointer;
            transition: all 0.3s ease;
            background-color: transparent;
            color: #4CAF50;
        }}
        .settings button:hover {{
            background-color: #4CAF50;
            color: white;
        }}
        .balloon-content {{
            padding: 10px;
            background-color: #ffffff;
            border-radius: 10px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            text-align: center;
        }}
        .balloon-content p {{
            margin: 0;
            margin-bottom: 10px;
            font-size: 14px;
            color: #333;
        }}
        .balloon-content button {{
            padding: 8px 16px;
            font-size: 14px;
            border-radius: 5px;
            border: none;
            cursor: pointer;
            background-color: #4CAF50;
            color: white;
            transition: background-color 0.3s ease, transform 0.3s ease;
        }}
        .balloon-content button:hover {{
            background-color: #45a049;
            transform: translateY(-2px);
        }}
    </style>
    <script type="text/javascript">
        var marks = {marks_json};
        var polygons = {polygons_json};
        var emergencyMarks = {emergency_marks_json};
        var lowTempPolygons = {low_temp_polygons_json};
        var highTempPolygons = {hight_temp_polygons_json};
        var noHeatingPolygons = {no_heating_polygons_json};
        var strongLeakPolygons = {strong_leak_polygons_json};
        var leakPolygons = {leak_polygons_json};

        var myMap;
        var placemarks = [];
        var polygonsOnMap = [];
        var emergencyPlacemarks = [];
        var criticalPolygonsOnMap = [];

        ymaps.ready(init);
        function init() {{
            myMap = new ymaps.Map("map", {{
                center: [55.7558, 37.6173],
                zoom: 11
            }});
        }}

        function loadMarks() {{
            marks.forEach(function(mark) {{
                var placemark = new ymaps.Placemark(mark.coords, {{
                    balloonContent: '<div class="balloon-content"><p>' + mark.name + '</p><button onclick="alert(\\"Кнопка нажата!\\")">Нажать</button></div>'
                }}, {{
                    preset: 'islands#circleIcon',
                    iconColor: '#1E98FF'
                }});
                myMap.geoObjects.add(placemark);
                placemarks.push(placemark);
                placemark.events.add('mouseenter', function (e) {{
                    placemark.options.set('preset', 'islands#redCircleIcon');
                }});
                placemark.events.add('mouseleave', function (e) {{
                    placemark.options.set('preset', 'islands#circleIcon');
                }});
            }});
        }}

        function loadPolygons() {{
            var color = document.getElementById("colorPicker").value;
            var opacity = document.getElementById("opacityRange").value / 100;
            var strokeOpacity = Math.min(opacity + 0.3, 1);

            polygons.forEach(function(polygonCoords) {{
                var fillColor = color + Math.floor(opacity * 255).toString(16).padStart(2, '0');
                var strokeColor = color + Math.floor(strokeOpacity * 255).toString(16).padStart(2, '0');

                var myPolygon = new ymaps.Polygon([polygonCoords], {{}}, {{
                    fillColor: fillColor,
                    strokeWidth: 5,
                    strokeColor: strokeColor,
                    opacity: opacity
                }});
                myMap.geoObjects.add(myPolygon);
                polygonsOnMap.push(myPolygon);
            }});
        }}

        function loadEmergencyMarks() {{
            emergencyMarks.forEach(function(emergencyMark) {{
                var emergencyPlacemark = new ymaps.Placemark(emergencyMark.coords, {{ balloonContent: emergencyMark.name }}, {{
                    iconLayout: 'default#image',
                    iconImageHref: 'https://pro-color.ru/wa-data/public/shop/products/97/56/5697/images/11853/11853.970.png',
                    iconImageSize: [32, 32],
                    iconImageOffset: [-16, -16]
                }});
                myMap.geoObjects.add(emergencyPlacemark);
                emergencyPlacemarks.push(emergencyPlacemark);
            }});
        }}

        function loadCriticalPolygons(criticalPolygons) {{
            var color = document.getElementById("colorPicker").value;
            var opacity = document.getElementById("opacityRange").value / 100;
            var strokeOpacity = Math.min(opacity + 0.3, 1);

            criticalPolygons.forEach(function(polygonCoords) {{
                var fillColor = color + Math.floor(opacity * 255).toString(16).padStart(2, '0');
                var strokeColor = color + Math.floor(strokeOpacity * 255).toString(16).padStart(2, '0');

                var myPolygon = new ymaps.Polygon([polygonCoords], {{}}, {{
                    fillColor: fillColor,
                    strokeWidth: 5,
                    strokeColor: strokeColor,
                    opacity: opacity
                }});
                myMap.geoObjects.add(myPolygon);
                criticalPolygonsOnMap.push(myPolygon);
            }});
        }}

        function clearAll() {{
            placemarks.forEach(function(placemark) {{
                myMap.geoObjects.remove(placemark);
            }});
            polygonsOnMap.forEach(function(polygon) {{
                myMap.geoObjects.remove(polygon);
            }});
            emergencyPlacemarks.forEach(function(emergencyPlacemark) {{
                myMap.geoObjects.remove(emergencyPlacemark);
            }});
            criticalPolygonsOnMap.forEach(function(polygon) {{
                myMap.geoObjects.remove(polygon);
            }});
            placemarks = [];
            polygonsOnMap = [];
            emergencyPlacemarks = [];
            criticalPolygonsOnMap = [];
        }}

        function handleSelection() {{
            var selectedValue = document.getElementById("selectMenu").value;
            if (selectedValue === "marks") {{
                loadMarks();
            }} else if (selectedValue === "polygons") {{
                loadPolygons();
            }} else if (selectedValue === "emergency_marks") {{
                loadEmergencyMarks();
            }} else {{
                // Обработка других значений
            }}
        }}

        function handleCriticalSelection() {{
            clearAll();
            var selectedValue = document.getElementById("criticalSelectMenu").value;
            if (selectedValue === "low_temp") {{
                loadCriticalPolygons(lowTempPolygons);
            }} else if (selectedValue === "high_temp") {{
                loadCriticalPolygons(highTempPolygons);
            }} else if (selectedValue === "no_heating") {{
                loadCriticalPolygons(noHeatingPolygons);
            }} else if (selectedValue === "strong_leak") {{
                loadCriticalPolygons(strongLeakPolygons);
            }} else if (selectedValue === "leak") {{
                loadCriticalPolygons(leakPolygons);
            }}
        }}

        function toggleSettings() {{
            var settings = document.getElementById('settings');
            if (settings.classList.contains('show')) {{
                settings.classList.remove('show');
                settings.classList.add('hide');
            }} else {{
                settings.classList.remove('hide');
                settings.classList.add('show');
            }}
        }}

        function dragElement(element) {{
            var pos1 = 0, pos2 = 0, pos3 = 0, pos4 = 0;
            var header = document.getElementById("settingsHeader");
            if (header) {{
                header.onmousedown = dragMouseDown;
            }}
            function dragMouseDown(e) {{
                if (e.target.tagName === "INPUT" || e.target.tagName === "BUTTON") {{
                    return;
                }}
                e = e || window.event;
                e.preventDefault();
                pos3 = e.clientX;
                pos4 = e.clientY;
                document.onmouseup = closeDragElement;
                document.onmousemove = elementDrag;
            }}

            function elementDrag(e) {{
                e = e || window.event;
                e.preventDefault();
                pos1 = pos3 - e.clientX;
                pos2 = pos4 - e.clientY;
                pos3 = e.clientX;
                pos4 = e.clientY;
                element.style.top = (element.offsetTop - pos2) + "px";
                element.style.left = (element.offsetLeft - pos1) + "px";
            }}

            function closeDragElement() {{
                document.onmouseup = null;
                document.onmousemove = null;
            }}
        }}

        function preventDrag(e) {{
            e.stopPropagation();
        }}

        function debounce(func, wait) {{
            let timeout;
            return function(...args) {{
                clearTimeout(timeout);
                timeout = setTimeout(() => {{
                    func.apply(this, args);
                }}, wait);
            }};
        }}

        document.addEventListener("DOMContentLoaded", function() {{
            dragElement(document.getElementById("settings"));
            document.getElementById("opacityRange").addEventListener("input", debounce(function() {{
                clearAll();
                loadPolygons();
            }}, 200));
        }});

        // Новая функция для обработки загрузки файлов
        function handleFileUpload(event) {{
            var file = event.target.files[0];
            if (file) {{
                var reader = new FileReader();
                reader.onload = function(e) {{
                    var data = JSON.parse(e.target.result);
                    if (data.marks) {{
                        marks = data.marks;
                    }}
                    if (data.polygons) {{
                        polygons = data.polygons;
                    }}
                    if (data.emergencyMarks) {{
                        emergencyMarks = data.emergencyMarks;
                    }}
                    clearAll();
                    handleSelection();
                }};
                reader.readAsText(file);
            }}
        }}
    </script>
</head>
<body>
    <div id="map"></div>
    <div class="controls">
            <span>Все объекты для ВАО:</span>
        <select id="selectMenu" onchange="handleSelection()">
            <option value="">Выберите данные</option>
            <option value="marks">Метки зданий</option>
            <option value="polygons">Полигоны зданий</option>
            <option value="emergency_marks">Метки всех аварийных зданий</option>
        </select>
        <span>Критические объекты по категориям:</span>
        <select id="criticalSelectMenu" onchange="handleCriticalSelection()">
            <option value="">Выберите данные</option>
            <option value="low_temp">Температура в квартире ниже нормативной</option>
            <option value="high_temp">T1 &gt; max</option>
            <option value="no_heating">Отсутствие отопления в доме</option>
            <option value="strong_leak">Сильная течь в системе отопления</option>
            <option value="leak">Течь в системе отопления</option>
        </select>
        <button onclick="clearAll()">Очистить все</button>
        <button onclick="toggleSettings()">Настройки</button>
        <!-- Новая кнопка для загрузки файлов -->
        <input type="file" id="fileUpload" accept=".json" onchange="handleFileUpload(event)">
        <label for="fileUpload">Загрузить файл</label>
    </div>
    <div id="settings" class="settings hide">
        <h3 id="settingsHeader">Настройки отображения</h3>
        <label for="colorPicker">Цвет полигонов:</label>
        <input type="color" id="colorPicker" value="#FF0000">
        <label for="opacityRange">Прозрачность полигонов:</label>
        <input type="range" id="opacityRange" min="0" max="100" value="50">
        <button onclick="toggleSettings()">Закрыть</button>
    </div>
</body>
</html>
"""

# Функция для запуска GUI приложения
def create_gui():
    window = webview.create_window(
        title='Сервис прогнозирования аварийности зданий',
        html=map_html,
        frameless=False,  # Рамка окна
        width=1500,
        height=1000,
        resizable=True,  # Окно можно изменять по размеру
        confirm_close=True,  # Запрос подтверждения при закрытии окна
        text_select=False,  # Запрещаем выделение текста
        background_color='#f0f0f0'  # Цвет фона окна
    )

    webview.start()

# Запуск GUI приложения
if __name__ == "__main__":
    create_gui()

