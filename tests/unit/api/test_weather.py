import pytest
from unittest.mock import patch
from requests.exceptions import RequestException
from app.api.weather import WeatherAPI


@patch.dict("os.environ", {"OPENWEATHER_API_KEY": "test_key"})
@patch("app.api.weather.requests.get")
def test_get_current_weather_success(mock_get):
    mock_get.return_value.json.return_value = {
        "name": "Москва",
        "sys": {"country": "RU"},
        "main": {"temp": 15.5, "feels_like": 14.2, "humidity": 60, "pressure": 1013},
        "weather": [{"description": "пасмурно", "icon": "04d"}],
        "wind": {"speed": 3.5, "deg": 180}
    }
    mock_get.return_value.raise_for_status = lambda: None

    api = WeatherAPI()
    result = api.get_current_weather("Москва")

    assert result["city"] == "Москва"
    assert result["temperature"] == 15.5
    assert result["weather"] == "Пасмурно"


@patch.dict("os.environ", {"OPENWEATHER_API_KEY": "test_key"})
@patch("app.api.weather.requests.get")
def test_get_current_weather_failure(mock_get):
    mock_get.side_effect = RequestException("Network error")

    api = WeatherAPI()
    result = api.get_current_weather("NonexistentCity")

    assert result is None