# Анализатор NLHE-раздач — план реализации

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Локальное приложение разбирает одну раздачу No-Limit Texas Hold'em: движок считает силу руки, эквити и решение по пот-оддсам, текст результата только пересказывает эти цифры. Статистика сессии и отчёт по ней — следующие фазы того же продукта.

**Architecture:** Чистая библиотека на Python считает всё, что является числом. Слой отчёта собирает `HandReport`. Текст пишет `Narrator`: офлайн-шаблон всегда доступен, LLM-провайдер необязателен и не имеет права менять цифры. CLI и локальная веб-страница — два тонких клиента одного и того же отчёта. Статистика сессии читает свои JSON-руки и не зависит от эквити одной раздачи.

**Tech Stack:** Python 3.12, pytest, FastAPI + uvicorn (фаза 2), httpx (только LLM-провайдер). Своя оценка руки и эквити, без PioSOLVER и без библиотек-оценщиков.

**Spec:** решения этого документа, раздел «Зафиксированные решения». Отдельного spec-файла нет: опрос по форме результата был прерван, допущения записаны здесь.

## Global Constraints

- Вариант игры: No-Limit Texas Hold'em. У героя ровно 2 карты, на борде 0, 3, 4 или 5 карт. Omaha, стад и лимитный холдем не входят.
- Эквити первой версии — против одного оппонента (конкретная рука или диапазон). Мультивей — вне плана.
- Числа считает только движок. Текст, включая LLM, цитирует `HandReport` и не подставляет другую эквити и другое действие.
- Рекомендация действия: `check`, если коллировать нечего; иначе `call` или `fold` по сравнению эквити с пот-оддсами. Рейз первая версия не рекомендует: фолд-эквити она не оценивает.
- Приложение разбирает раздачу, которую пользователь ввёл для учёбы. Подсказки вживую за столом онлайн-рума (RTA) не делаем.
- Пот в отчёте — банк, в который уже входит ставка оппонента и ещё не входит колл героя. Доля банка для колла: `to_call / (pot + to_call)`.
- Деньги в одной раздаче — целые фишки `>= 0`. `to_call == 0` означает, что решения колл/фолд нет.
- Тесты эквити с полным перебором сравнивают доли точно. Монте-Карло сравнивает с известным ориентиром в допуске, с фиксированным `seed`.
- Комбинации диапазона равновероятны. Веса рук не поддерживаются.
- Язык текста результата — русский. Код, имена модулей и коммит-сообщения — английский.
- Секреты только из окружения (`POKER_HANDLINE_LLM_API_KEY`, `POKER_HANDLINE_LLM_BASE_URL`, `POKER_HANDLINE_LLM_MODEL`). В репозиторий ключ не попадает.

---

## С чего начинается работа

Конечный продукт — одно приложение из трёх слоёв, а не три отдельные программы.

1. Факты раздачи: игроки, позиции, стеки, карты героя, борд, банк, сколько нужно коллировать, что уже произошло. Факты вводятся формой или файлом истории после сессии.
2. Движок: сила руки, эквити, пот-оддсы, статистика сохранённых рук. Этот слой не вызывает модель.
3. Итог: действие `fold` / `call` / `check` из сравнения эквити с ценой колла и короткий русский текст, который повторяет цифры движка.

Начинать со слоя 2. Пока программа не отличает стрит от фулл-хауса и не считает эквити на известной раздаче, слоям 1 и 3 нечего показывать.

Живой захват экрана покер-рума и совет «ставь столько-то в этой раздаче сейчас» в этот продукт не входят: румы считают это читерством, а размер ставки модель сама не знает.

## Зафиксированные решения

Сделано по ответам:

1. Первая поставка — движок и разбор одной раздачи. Статистика сессии идёт после этого и в этом файле расписана как фаза 3–4, чтобы не смешивать её с оценщиком.
2. Движок — NLHE: 2 карты героя, борд до 5 карт, категория руки и эквити.

Принято как допуск, потому что выбор формы результата был отменён. Если нужно другое — правится этот раздел до кода:

3. Результат одной раздачи: название руки, эквити против руки или диапазона, требуемая эквити колла, действие `fold` / `call` / `check`, русский абзац.
4. Полный разбор каждого действия по улицам (бет/рейз/чек по линии) в первую поставку не входит. Для него нужна история действий и модель фолд-эквити; это отдельный план после фазы 2.
5. Свой оценщик, а не `treys` / `pokerkit`: правила короткие, тесты фиксируют комбинации, зависимость не скрывает ошибку кикера. Скорость префлоп-эквити закрывает монте-Карло, а не таблица на 2.5 млн рук.
6. Офлайн-шаблон обязателен. LLM — вторая реализация того же протокола `Narrator`, включается ключом. Так приложение работает без сети, а агент не становится источником чисел.

Порядок фаз:

| Фаза | Что появляется | Когда считать готовым |
| --- | --- | --- |
| 1 | Библиотека + CLI одной раздачи | Тесты оценщика, точной эквити и пот-оддсов зелёные, CLI печатает отчёт без ключа API |
| 2 | Локальная страница с той же формой | `TestClient` отдаёт отчёт, шаблон и отказ при мусорных картах |
| 3 | Статистика по списку рук в JSON | VPIP, PFR, AF, CBet, WTSD, W$SD, результат в бб на фиксированной выборке |
| 4 | Текст по статистике сессии | Агент цитирует посчитанные проценты и помечает выход за учебные коридоры |

Фазы 3 и 4 не начинать, пока CLI фазы 1 не проходит свои тесты.

## Карта файлов

```text
pyproject.toml
src/poker_handline/__init__.py
src/poker_handline/cards.py           # Card, колода, разбор "As"
src/poker_handline/evaluator.py       # 5 карт и лучшие 5 из 6–7
src/poker_handline/ranges.py          # нотация диапазона → набор комбо
src/poker_handline/equity.py          # exact и monte carlo
src/poker_handline/report.py          # HandReport, пот-оддсы, действие
src/poker_handline/narrate.py         # TemplateNarrator и LLMNarrator
src/poker_handline/cli.py
src/poker_handline/api.py             # фаза 2
src/poker_handline/web/index.html     # фаза 2
src/poker_handline/stats.py           # фаза 3
src/poker_handline/session_narrate.py # фаза 4
tests/test_cards.py
tests/test_evaluator.py
tests/test_ranges.py
tests/test_equity.py
tests/test_report.py
tests/test_narrate.py
tests/test_cli.py
tests/test_api.py                     # фаза 2
tests/test_stats.py                   # фаза 3
tests/test_session_narrate.py         # фаза 4
```

Каждый файл фазы 1 — одна обязанность. Оценщик не знает про банк. Эквити не выбирает фолд. Нарратор не импортирует `equity.py`, он читает уже собранный `HandReport`.

## Контракты, на которые опираются задачи

```python
# cards.py
@dataclass(frozen=True, order=True)
class Card:
    rank: int  # 2..14
    suit: str  # "s" | "h" | "d" | "c"

def parse_card(text: str) -> Card: ...
def parse_cards(text: str) -> tuple[Card, ...]: ...
def deck() -> tuple[Card, ...]: ...  # 52 карты, порядок детерминированный

# evaluator.py
@dataclass(frozen=True)
class HandRank:
    category: int  # 8 стрит-флеш … 0 старшая карта
    kickers: tuple[int, ...]
    name: str

    def key(self) -> tuple[int, tuple[int, ...]]:
        return (self.category, self.kickers)

def rank_five(cards: Sequence[Card]) -> HandRank: ...
def best_hand(cards: Sequence[Card]) -> HandRank: ...  # 5, 6 или 7 карт

# ranges.py
Combo = frozenset[Card]  # всегда 2 карты

def expand_range(notation: str, dead: Collection[Card] = ()) -> frozenset[Combo]: ...

# equity.py
@dataclass(frozen=True)
class EquityResult:
    win: float
    tie: float
    lose: float
    trials: int
    method: Literal["exact", "monte_carlo"]

    @property
    def share(self) -> float:
        return self.win + self.tie / 2.0

def equity(
    hero: str,
    villain: str,
    board: str = "",
    *,
    trials: int = 10_000,
    seed: int = 0,
) -> EquityResult: ...

# report.py
Action = Literal["fold", "call", "check"]

@dataclass(frozen=True)
class HandReport:
    hero: tuple[str, str]
    board: tuple[str, ...]
    villain: str
    hand_name: str
    equity: EquityResult
    pot: int
    to_call: int
    required_equity: float | None
    action: Action

def build_report(
    hero: str,
    board: str,
    villain: str,
    pot: int,
    to_call: int,
    *,
    trials: int = 10_000,
    seed: int = 0,
) -> HandReport: ...

# narrate.py
class Narrator(Protocol):
    def narrate(self, report: HandReport) -> str: ...

class TemplateNarrator:
    def narrate(self, report: HandReport) -> str: ...

class LLMNarrator:
    def __init__(self, base_url: str, api_key: str, model: str, transport: httpx.BaseTransport | None = None) -> None: ...
    def narrate(self, report: HandReport) -> str: ...
```

Сравнение рук — по `HandRank.key()`, не по имени. `роял-флеш` и обычный стрит-флеш оба имеют category `8`; старше тот, у кого больше старшая карта стрита.

---

## Фаза 1. Движок и CLI

### Task 1: Каркас пакета

**Files:**
- Create: `pyproject.toml`
- Create: `src/poker_handline/__init__.py`
- Create: `tests/test_cards.py` (пустой импорт появится в задаче 2; здесь только конфиг)

**Interfaces:**
- Consumes: нет
- Produces: пакет `poker_handline`, команда `pytest`

- [x] **Step 1: Добавить `pyproject.toml`**

```toml
[project]
name = "poker-handline"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = []

[project.optional-dependencies]
app = ["fastapi>=0.115", "uvicorn>=0.32"]
llm = ["httpx>=0.27"]

[project.scripts]
poker-handline = "poker_handline.cli:main"

[build-system]
requires = ["setuptools>=69"]
build-backend = "setuptools.build_meta"

[tool.setuptools.packages.find]
where = ["src"]

[tool.setuptools.package-data]
poker_handline = ["web/index.html"]

[tool.pytest.ini_options]
pythonpath = ["src"]
testpaths = ["tests"]
```

- [x] **Step 2: Пустой пакет**

`src/poker_handline/__init__.py` содержит версию:

```python
__version__ = "0.1.0"
```

- [x] **Step 3: Установить и проверить, что pytest запускается**

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python -m pip install -e ".[app,llm]" pytest
.\.venv\Scripts\python -m pytest
```

Ожидание: `no tests ran` и код выхода 5, либо 0 если pytest настроен с `--override-ini` не нужен. Достаточно, что интерпретатор 3.12 и pytest импортируются. Если `py -3.12` нет, остановиться и поставить 3.12, а не писать под 3.11: в аннотациях ниже используется синтаксис 3.12.

- [x] **Step 4: Commit**

```powershell
git add pyproject.toml src/poker_handline/__init__.py
git commit -m "chore: scaffold poker-handline package"
```

### Task 2: Карты и колода

**Files:**
- Create: `src/poker_handline/cards.py`
- Create: `tests/test_cards.py`

**Interfaces:**
- Consumes: нет
- Produces: `Card`, `parse_card`, `parse_cards`, `deck`

- [ ] **Step 1: Падающий тест**

```python
import pytest

from poker_handline.cards import Card, deck, parse_card, parse_cards


def test_parse_card_rank_and_suit():
    assert parse_card("As") == Card(14, "s")
    assert parse_card("Td") == Card(10, "d")
    assert parse_card("2c") == Card(2, "c")


def test_parse_cards_splits_on_spaces_and_concat():
    assert parse_cards("As Kh") == (Card(14, "s"), Card(13, "h"))
    assert parse_cards("AsKh") == (Card(14, "s"), Card(13, "h"))
    assert parse_cards("") == ()


def test_ten_is_letter_t_not_digit_10():
    with pytest.raises(ValueError):
        parse_card("10s")


def test_duplicate_and_junk_rejected():
    with pytest.raises(ValueError):
        parse_cards("As As")
    with pytest.raises(ValueError):
        parse_card("Ax")
    with pytest.raises(ValueError):
        parse_card("1s")


def test_deck_has_52_unique_cards():
    cards = deck()
    assert len(cards) == 52
    assert len(set(cards)) == 52
    assert Card(14, "s") in cards
    assert cards == deck()
```

- [ ] **Step 2: Запустить тест и увидеть импорт-ошибку**

```powershell
.\.venv\Scripts\python -m pytest tests/test_cards.py -v
```

Ожидание: FAIL, модуль `cards` не найден.

- [ ] **Step 3: Реализация**

Ранги: `2 3 4 5 6 7 8 9 T J Q K A` → `2..14`. Масти: `s h d c`. Регистр буквы ранга не важен, масть приводится к нижнему. `parse_cards` удаляет пробелы и режет строку по 2 символа. Повтор карты и нечётная длина — `ValueError`. `deck` — двойной цикл мастей `s,h,d,c` и рангов от 2 до 14.

- [ ] **Step 4: Тест зелёный**

```powershell
.\.venv\Scripts\python -m pytest tests/test_cards.py -v
```

Ожидание: PASS.

- [ ] **Step 5: Commit**

```powershell
git add src/poker_handline/cards.py tests/test_cards.py
git commit -m "feat: parse cards and build a 52-card deck"
```

### Task 3: Оценка пяти карт

**Files:**
- Create: `src/poker_handline/evaluator.py`
- Create: `tests/test_evaluator.py`

**Interfaces:**
- Consumes: `Card`, `parse_cards`
- Produces: `HandRank`, `rank_five`

Категории, от старшей к младшей: 8 стрит-флеш (роял-флеш — то же 8 со старшей картой 14 и именем `роял-флеш`), 7 каре, 6 фулл-хаус, 5 флеш, 4 стрит, 3 тройка, 2 две пары, 1 пара, 0 старшая карта.

- [ ] **Step 1: Падающий тест**

```python
from poker_handline.cards import parse_cards
from poker_handline.evaluator import rank_five


def rank(text: str):
    return rank_five(parse_cards(text))


def test_categories_and_names():
    assert rank("As Ks Qs Js Ts").name == "роял-флеш"
    assert rank("9h 8h 7h 6h 5h").key() == (8, (9,))
    assert rank("As Ks Qs Js Ts").key() > rank("9h 8h 7h 6h 5h").key()
    assert rank("Ah Ad Ac As Kd").key() == (7, (14, 13))
    assert rank("Kh Kd Kc 2s 2d").key() == (6, (13, 2))
    assert rank("Ah Ad Ac Ks Kd").key() > rank("Kh Kd Kc As Ad").key()
    assert rank("Ah Kh Qh Jh 9h").key() == (5, (14, 13, 12, 11, 9))
    assert rank("As Kd Qc Jh Td").key() == (4, (14,))
    assert rank("As 2d 3c 4h 5s").key() == (4, (5,))
    assert rank("As Kd Qc Jh Td").key() > rank("As 2d 3c 4h 5s").key()
    assert rank("Th Td Tc Ks Qd").key() == (3, (10, 13, 12))
    assert rank("Ah Ad Kh Kd 2c").key() == (2, (14, 13, 2))
    assert rank("Ah Ad Kh Kd Qc").key() > rank("Ah Ad Qh Qd Kc").key()
    assert rank("Ah Ad Ks Qd Jc").key() == (1, (14, 13, 12, 11))
    assert rank("Ah Kd Qc Jh 9s").key() == (0, (14, 13, 12, 11, 9))


def test_wheel_is_not_a_broadway_straight():
    assert rank("As 2d 3c 4h 5s").name == "стрит"
    assert rank("Ah 2h 3h 4h 5h").name == "стрит-флеш"
    assert rank("Ah 2h 3h 4h 5h").key() == (8, (5,))


def test_pair_kicker_order():
    assert rank("Ah Ad Ks Qd 2c").key() > rank("Ah Ad Qs Jd 9c").key()
```

- [ ] **Step 2: Убедиться, что тест падает**

```powershell
.\.venv\Scripts\python -m pytest tests/test_evaluator.py -v
```

Ожидание: FAIL, `rank_five` не определён.

- [ ] **Step 3: Реализация `rank_five`**

Отсортировать ранги по убыванию. Флеш — одна масть. Стрит — пять разных рангов, у которых `max - min == 4`, либо набор `{14, 5, 4, 3, 2}` со старшей картой стрита `5` (колесо не бьёт шестёрку-старшую). Иначе старшая карта стрита — максимальный ранг.

Дальше `Counter` рангов, пары сортируются по `(count, rank)` по убыванию:

- стрит и флеш → category 8, кикер `(straight_high,)`, имя `роял-флеш` только если `straight_high == 14`, иначе `стрит-флеш`
- count 4 → category 7, кикеры `(квад, кикер)`
- 3 + 2 → category 6, кикеры `(тройка, пары)`
- флеш → category 5, кикеры — все пять рангов по убыванию
- стрит → category 4, кикер `(straight_high,)`
- тройка → category 3, кикеры `(тройка, старший кикер, младший)`
- две пары → category 2, кикеры `(старшая пара, младшая пара, кикер)`
- пара → category 1
- иначе category 0 и пять рангов

`HandRank.key` возвращает `(category, kickers)`. Сравнение в тестах идёт через него. Не включать `name` в ключ: у роял-флеша и стрит-флеша сравнение только по старшей карте.

Пять карт с повтором ранга больше четырёх или с дублем одной и той же карты в этот модуль не попадают: дубли ловит `parse_cards`, а `rank_five` предполагает уже различные `Card`.

- [ ] **Step 4: Тест зелёный**

```powershell
.\.venv\Scripts\python -m pytest tests/test_evaluator.py tests/test_cards.py -v
```

Ожидание: PASS.

- [ ] **Step 5: Commit**

```powershell
git add src/poker_handline/evaluator.py tests/test_evaluator.py
git commit -m "feat: rank five-card hold'em hands"
```

### Task 4: Лучшие пять из шести и семи

**Files:**
- Modify: `src/poker_handline/evaluator.py`
- Modify: `tests/test_evaluator.py`

**Interfaces:**
- Consumes: `rank_five`
- Produces: `best_hand(cards) -> HandRank`

- [ ] **Step 1: Падающий тест**

```python
import pytest

from poker_handline.cards import parse_cards
from poker_handline.evaluator import best_hand


def test_seven_cards_picks_full_house_not_two_pair():
    cards = parse_cards("Ah Ad As Kd Kc 2c 2d")
    assert best_hand(cards).key() == (6, (14, 13))
    assert best_hand(cards).name == "фулл-хаус"


def test_player_plays_the_board_flush():
    cards = parse_cards("2c 3d Ah Kh Qh Jh 9h")
    assert best_hand(cards).name == "флеш"
    assert best_hand(cards).key() == (5, (14, 13, 12, 11, 9))


def test_six_cards_drops_the_small_kicker():
    cards = parse_cards("Ah Ad Ks Qd Jc 2c")
    assert best_hand(cards).key() == (1, (14, 13, 12, 11))


def test_board_length_other_than_five_six_seven_rejected():
    with pytest.raises(ValueError):
        best_hand(parse_cards("As Kd Qc Jh"))
```

- [ ] **Step 2: Убедиться, что тест падает**

```powershell
.\.venv\Scripts\python -m pytest tests/test_evaluator.py::test_seven_cards_picks_full_house_not_two_pair -v
```

Ожидание: FAIL, `best_hand` не определён.

- [ ] **Step 3: Реализация**

`best_hand` принимает 5, 6 или 7 различных карт. Для каждой комбинации `itertools.combinations(cards, 5)` считает `rank_five` и оставляет максимум по `key()`. На 7 картах это 21 комбинация.

- [ ] **Step 4: Тест зелёный**

```powershell
.\.venv\Scripts\python -m pytest tests/test_evaluator.py -v
```

Ожидание: PASS.

- [ ] **Step 5: Commit**

```powershell
git add src/poker_handline/evaluator.py tests/test_evaluator.py
git commit -m "feat: choose the best five cards from six or seven"
```

### Task 5: Нотация диапазона

**Files:**
- Create: `src/poker_handline/ranges.py`
- Create: `tests/test_ranges.py`

**Interfaces:**
- Consumes: `Card`, `parse_cards`, `deck`
- Produces: `expand_range(notation, dead=()) -> frozenset[frozenset[Card]]`

Грамматика, пробелы вокруг запятых игнорируются:

- `AsKh` — одна конкретная комбинация. Карты можно писать и через пробел внутри терма, если терм один. В списке через запятую пробел — разделитель только вокруг запятой, не внутри `AsKh`.
- `QQ` — 6 комбинаций дам. `AK` — 16 комбинаций (4 suited + 12 offsuit). `AKs` — 4. `AKo` — 12.
- `QQ+` — пары от QQ до AA включительно.
- `ATs+` — suited туз с второй картой от T до K: ATs, AJs, AQs, AKs. `ATo+` — то же offsuit. Плюс не добавляет пару тузов.
- `22+` — все пары.
- `random` — все 1326 комбинаций.
- `QQ+,AKs` — объединение.
- Карта из `dead` выкидывает любую комбинацию, которая её содержит. Пустой результат — `ValueError`.
- Неизвестный токен (`AKz`, `QQ-`, `AKs+s`) — `ValueError`.

- [ ] **Step 1: Падающий тест**

```python
import pytest

from poker_handline.cards import parse_card, parse_cards
from poker_handline.ranges import expand_range


def test_concrete_hand_and_pair_combos():
    assert len(expand_range("AsKh")) == 1
    assert len(expand_range("QQ")) == 6
    assert len(expand_range("AKs")) == 4
    assert len(expand_range("AKo")) == 12
    assert len(expand_range("AK")) == 16


def test_plus_ranges_do_not_include_a_pair_of_aces_for_suited():
    pairs = expand_range("QQ+")
    assert len(pairs) == 6 + 6 + 6  # QQ KK AA
    suited = expand_range("ATs+")
    assert len(suited) == 4 * 4  # AT AJ AQ AK suited
    assert all(len(combo) == 2 for combo in suited)


def test_random_and_union():
    assert len(expand_range("random")) == 1326
    assert len(expand_range("QQ+,AKs")) == 18 + 4


def test_dead_cards_remove_combos():
    dead = parse_cards("As Ah")
    remaining = expand_range("AA", dead)
    assert len(remaining) == 1  # только AdAc
    with pytest.raises(ValueError):
        expand_range("AsKh", parse_cards("As"))


def test_bad_token():
    with pytest.raises(ValueError):
        expand_range("AKz")
```

- [ ] **Step 2: Убедиться, что тест падает**

```powershell
.\.venv\Scripts\python -m pytest tests/test_ranges.py -v
```

Ожидание: FAIL, модуль `ranges` не найден.

- [ ] **Step 3: Реализация**

Разбить по запятой. Для токена:

1. `random` → все сочетания колоды по 2.
2. Если длина 4 и оба полукарточных куска — валидные карты (`AsKh`), вернуть одну комбинацию, если обе карты живы.
3. Суффикс `+` снять флагом `plus`.
4. Окончание `s` или `o` снять как `suited` / `offsuit`. Оставшиеся два символа — ранги.
5. Одинаковые ранги — пары. С `plus` — от этого ранга до туза. `s`/`o` на паре — ошибка.
6. Разные ранги — непара. Без `s`/`o` и без `plus` — все 16. С `s` или `o` — только эти 4 или 12. С `plus` второй ранг (меньший) идёт вверх до ранга на один ниже старшего. Старший ранг в `ATs+` — туз; меньший старт — T. Запретить `plus`, если меньший ранг не строго меньше старшего.

Комбинация — `frozenset` из двух `Card`. Пересечение с `dead` удаляет комбо. Пустое множество после фильтра — `ValueError` с текстом нотации.

- [ ] **Step 4: Тест зелёный**

```powershell
.\.venv\Scripts\python -m pytest tests/test_ranges.py -v
```

Ожидание: PASS.

- [ ] **Step 5: Commit**

```powershell
git add src/poker_handline/ranges.py tests/test_ranges.py
git commit -m "feat: expand hold'em range notation into combos"
```

### Task 6: Эквити

**Files:**
- Create: `src/poker_handline/equity.py`
- Create: `tests/test_equity.py`

**Interfaces:**
- Consumes: `parse_cards`, `best_hand`, `expand_range`, `deck`
- Produces: `EquityResult`, `equity`

Правило выбора метода внутри `equity`:

- неизвестных карт борда 0, 1 или 2 (ривер, тёрн, флоп) — полный перебор, `method="exact"`, `trials` равен числу перебранных раскладов
- борда нет (префлоп, 5 неизвестных) — монте-Карло, `method="monte_carlo"`, `trials` как в аргументе
- борд из 1 или 2 карт — `ValueError` (в холдеме так не бывает)

Доли: на каждом раскладе сравнить `best_hand(hero + board_full)` и `best_hand(villain + board_full)`. Победа / ничья / поражение героя делятся на число раскладов. Для диапазона каждый комбо равновероятный: внешний цикл по комбо, внутренний по добору борда, знаменатель — сумма раскладов, а не число комбо. Комбо, пересекающиеся с героем или бордом, в диапазон уже не входят.

`share = win + tie / 2`.

- [ ] **Step 1: Падающий тест**

```python
from poker_handline.equity import equity


def test_river_royal_beats_a_pair_exactly():
    result = equity("AhKh", "2d2s", "Qh Jh Th 2c 3d")
    assert result.method == "exact"
    assert result.win == 1.0
    assert result.tie == 0.0
    assert result.share == 1.0


def test_river_same_straight_splits_exactly():
    result = equity("AsKd", "AhKc", "Qs Js Tc 2c 3d")
    assert result.tie == 1.0
    assert result.share == 0.5


def test_turn_flush_draw_versus_overpair_is_nine_hearts():
    # 8h7h против QcQd на Ah Kh 2c 3d. Пара дам без сета.
    # Из 44 живых карт выигрывают ровно 9 оставшихся черв:
    # 2h 3h 4h 5h 6h 9h Th Jh Qh. Флеш бьёт и QQ, и фулл-хаус тут не собирается.
    # Qh даёт злодею сет, но флеш старше сета. 2h и 3h тоже остаются аутами.
    result = equity("8h7h", "QcQd", "Ah Kh 2c 3d")
    assert result.method == "exact"
    assert result.trials == 44
    assert result.win == 9 / 44
    assert result.tie == 0.0
    assert result.lose == 35 / 44


def test_preflop_aces_versus_kings_is_about_82_percent():
    result = equity("AsAh", "KdKh", trials=8_000, seed=1)
    assert result.method == "monte_carlo"
    assert result.trials == 8_000
    assert abs(result.share - 0.822) < 0.03


def test_flop_is_exact_and_partial_board_rejected():
    import pytest

    flop = equity("AsKh", "QQ", "Td 9c 2s", trials=100, seed=1)
    assert flop.method == "exact"
    with pytest.raises(ValueError):
        equity("AsKh", "QQ", "Td")
```

- [ ] **Step 2: Убедиться, что тест падает**

```powershell
.\.venv\Scripts\python -m pytest tests/test_equity.py -v
```

Ожидание: FAIL, модуль `equity` не найден.

- [ ] **Step 3: Реализация**

Проверить: у героя 2 карты, борд 0/3/4/5, пересечений карт нет. `expand_range(villain, dead=hero+board)`.

Exact: недостающие карты взять из колоды без мёртвых. Для ривера один пустой добор. Для тёрна — каждая из оставшихся карт. Для флопа — сочетания по 2. Не использовать случайность в этой ветке.

Monte Carlo (только пустой борд): `random.Random(seed)`, на каждый trial выбрать 5 карт борда из оставшейся колоды без изъятия комбо из пула между trial (выбор с возвратом колоды, без возврата внутри одного trial). Комбо злодея на trial выбирать равномерно из `expand_range`. Если у конкретного комбо не хватает пяти карт — пропустить этот комбо ещё на этапе expand, до цикла.

Не писать отдельный «приблизительный» флоп: флоп и тёрн в тестах выше обязаны быть exact.

- [ ] **Step 4: Тест зелёный**

```powershell
.\.venv\Scripts\python -m pytest tests/test_equity.py -v
```

Ожидание: PASS. Префлоп-тест с 8000 trial должен укладываться в 3 процентных пункта при `seed=1`. Если на этой машине вылез за допуск — не расширять допуск молча; сначала проверить, что сид реально передаётся в `random.Random` и что ничьи считаются как половина.

- [ ] **Step 5: Commit**

```powershell
git add src/poker_handline/equity.py tests/test_equity.py
git commit -m "feat: compute heads-up equity exactly and by monte carlo"
```

### Task 7: Отчёт одной раздачи и пот-оддсы

**Files:**
- Create: `src/poker_handline/report.py`
- Create: `tests/test_report.py`

**Interfaces:**
- Consumes: `equity`, `best_hand`, `parse_cards`
- Produces: `HandReport`, `build_report`

Имя руки в отчёте — `best_hand(hero + board).name`. На префлопе борд пустой, и имя руки — категория двух карт: для пары `пара`, иначе `старшая карта`. Не выдумывать «карманные тузы» отдельной категорией оценщика: две карты не идут в `rank_five`. Отдельная функция `hole_name(hero) -> str` возвращает `пара`, если ранги совпали, иначе `старшая карта`.

Действие:

- `pot < 0` или `to_call < 0` → `ValueError`
- `to_call == 0` → `action="check"`, `required_equity=None`
- `to_call > 0` → `required_equity = to_call / (pot + to_call)`. Если `equity.share + 1e-12 >= required_equity` → `call`, иначе `fold`

- [ ] **Step 1: Падающий тест**

```python
import pytest

from poker_handline.report import build_report


def test_call_when_equity_covers_the_price():
    # Ривер, у героя роял-флеш, эквити 100%. Банк 100, колл 50 → нужно 1/3.
    report = build_report("AhKh", "Qh Jh Th 2c 3d", "2d2s", pot=100, to_call=50)
    assert report.hand_name == "роял-флеш"
    assert report.required_equity == pytest.approx(50 / 150)
    assert report.action == "call"
    assert report.equity.share == 1.0


def test_fold_when_draw_does_not_cover_a_large_bet():
    # Та же раздача, что в тесте эквити: share = 9/44 ≈ 20,5%.
    # Нужно 50 / (10 + 50) ≈ 83%.
    report = build_report("8h7h", "Ah Kh 2c 3d", "QcQd", pot=10, to_call=50)
    assert report.equity.share == pytest.approx(9 / 44)
    assert report.action == "fold"


def test_check_when_nothing_to_call():
    report = build_report("AsAh", "", "KdKh", pot=10, to_call=0, trials=200, seed=1)
    assert report.hand_name == "пара"
    assert report.required_equity is None
    assert report.action == "check"


def test_negative_money_rejected():
    with pytest.raises(ValueError):
        build_report("AsKh", "Td 9c 2s", "QQ", pot=-1, to_call=0)
```

- [ ] **Step 2: Убедиться, что тест падает**

```powershell
.\.venv\Scripts\python -m pytest tests/test_report.py -v
```

Ожидание: FAIL, модуль `report` не найден.

- [ ] **Step 3: Реализация**

`build_report` вызывает `equity`, затем выставляет имя и действие по правилам выше. Поля `hero`, `board`, `villain` хранят уже нормализованный ввод: карты через `parse_cards`, в отчёт кладутся как `f"{rank_char}{suit}"` в том порядке, в котором их распарсили. Для туза пики — `As`, для десятки — `Td`.

Никакого рейза и никакого размера ставки. При `to_call == 0` шаблон из задачи 8 говорит, что размер ставки эта версия не выбирает.

- [ ] **Step 4: Тест зелёный**

```powershell
.\.venv\Scripts\python -m pytest tests/test_report.py -v
```

Ожидание: PASS.

- [ ] **Step 5: Commit**

```powershell
git add src/poker_handline/report.py tests/test_report.py
git commit -m "feat: turn equity and pot odds into a hand report"
```

### Task 8: Текст результата

**Files:**
- Create: `src/poker_handline/narrate.py`
- Create: `tests/test_narrate.py`

**Interfaces:**
- Consumes: `HandReport`
- Produces: `TemplateNarrator`, `LLMNarrator`

Шаблон для `call` и `fold`:

```text
{hand_name}. Эквити против {villain}: {share_pct}. Для колла нужно {required_pct}. Решение движка: {action_ru}.
Движок не оценивает фолд-эквити рейза и выбирает только колл или фолд.
```

Шаблон для `check`:

```text
{hand_name}. Эквити против {villain}: {share_pct}. Ставки для колла нет. Решение движка: чек.
Размер ставки эта версия не рекомендует.
```

`share_pct` и `required_pct` — проценты с одним знаком после запятой, десятичный разделитель — запятая (`82,2%`). `action_ru`: fold → `фолд`, call → `колл`, check → `чек`.

`LLMNarrator` шлёт chat-completions на OpenAI-совместимый URL. В system-промпте дословно:

```text
Ты объясняешь уже посчитанный отчёт по одной раздаче NLHE. Пиши по-русски, 4–6 предложений.
Повтори название руки, эквити и действие ровно такими, как в JSON. Не считай эквити заново.
Не рекомендуй рейз и не меняй fold, call или check. Если действия check, не предлагай размер ставки.
```

User-сообщение — `json.dumps` отчёта с полями `hand_name`, `villain`, `equity_share`, `required_equity`, `action`, `method`. Ответ модели прогоняется через проверку: в тексте есть `hand_name`, есть процент эквити в том виде, в каком его печатает шаблон (`82,2%`), и есть русское слово действия. Если проверки нет — `ValueError`, наружу отдаётся текст шаблона. Вызывающий код ловит ошибку провайдера и тоже отдаёт шаблон: сеть не должна ломать CLI.

- [ ] **Step 1: Падающий тест**

```python
import json

import httpx
import pytest

from poker_handline.narrate import LLMNarrator, TemplateNarrator
from poker_handline.report import build_report


def test_template_call_quotes_engine_numbers():
    report = build_report("AhKh", "Qh Jh Th 2c 3d", "2d2s", pot=100, to_call=50)
    text = TemplateNarrator().narrate(report)
    assert "роял-флеш" in text
    assert "100,0%" in text
    assert "33,3%" in text
    assert "колл" in text
    assert "рейза" in text


def test_template_check_does_not_invent_a_bet():
    report = build_report("AsAh", "", "KdKh", pot=10, to_call=0, trials=50, seed=1)
    text = TemplateNarrator().narrate(report)
    assert "чек" in text
    assert "не рекомендует" in text


def test_llm_narrator_rejects_a_changed_action():
    report = build_report("AhKh", "Qh Jh Th 2c 3d", "2d2s", pot=100, to_call=50)

    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        assert "Не считай эквити заново" in body["messages"][0]["content"]
        return httpx.Response(200, json={"choices": [{"message": {"content": "Лучше рейз."}}]})

    transport = httpx.MockTransport(handler)
    narrator = LLMNarrator("http://llm.test/v1", "test-key", "test-model", transport=transport)
    with pytest.raises(ValueError):
        narrator.narrate(report)
```

Зависимость `httpx` в этом тесте — из extra `llm`. Установить её в окружение ещё в задаче 1 (`pip install -e ".[app,llm]"`).

- [ ] **Step 2: Убедиться, что тест падает**

```powershell
.\.venv\Scripts\python -m pytest tests/test_narrate.py -v
```

Ожидание: FAIL, модуль `narrate` не найден.

- [ ] **Step 3: Реализация**

`TemplateNarrator.narrate` форматирует один из двух абзацев. Процент: `f"{value * 100:.1f}".replace(".", ",") + "%"`.

`LLMNarrator.narrate` использует `httpx.Client(transport=transport, timeout=30)` если transport передан, иначе обычный клиент. POST `{base_url}/chat/completions`, заголовок `Authorization: Bearer {api_key}`. После ответа вызвать ту же процентную форму, что и шаблон, и проверить вхождение. Провал проверки — `ValueError`. Этот класс сам на шаблон не откатывается: откат делает CLI, чтобы тест видел отказ.

- [ ] **Step 4: Тест зелёный**

```powershell
.\.venv\Scripts\python -m pytest tests/test_narrate.py -v
```

Ожидание: PASS.

- [ ] **Step 5: Commit**

```powershell
git add src/poker_handline/narrate.py tests/test_narrate.py
git commit -m "feat: narrate a hand report without replacing engine numbers"
```

### Task 9: CLI

**Files:**
- Create: `src/poker_handline/cli.py`
- Create: `tests/test_cli.py`

**Interfaces:**
- Consumes: `build_report`, `TemplateNarrator`, `LLMNarrator`
- Produces: `main(argv: list[str] | None = None) -> int`

Вызов:

```powershell
python -m poker_handline.cli --hero AsKh --board "Td 9c 2s" --villain QQ+ --pot 100 --to-call 50
```

Пустой борд: `--board ""` или флаг опущен. Печать в stdout:

```text
Рука: роял-флеш
Эквити: 100,0% (win 100,0 / tie 0,0 / lose 0,0), exact, 1 раскладов
Нужно для колла: 33,3%
Решение: call
---
<абзац нарратора>
```

Для чека строка «Нужно для колла» заменяется на `Нужно для колла: нет`.

Код выхода 0 при успехе, 2 при `ValueError` (текст ошибки в stderr). Если заданы все три переменные `POKER_HANDLINE_LLM_BASE_URL`, `POKER_HANDLINE_LLM_API_KEY`, `POKER_HANDLINE_LLM_MODEL`, CLI пробует `LLMNarrator` и при любом исключении печатает шаблон. Без переменных сразу шаблон. Тест LLM в CLI не ходит в сеть: подменить нарратор функцией-фабрикой `narrator_factory`, аргумент `main`.

- [ ] **Step 1: Падающий тест**

```python
import pytest

from poker_handline.cli import main


def test_cli_prints_call(capsys):
    code = main(
        ["--hero", "AhKh", "--board", "Qh Jh Th 2c 3d", "--villain", "2d2s", "--pot", "100", "--to-call", "50"]
    )
    out = capsys.readouterr().out
    assert code == 0
    assert "Рука: роял-флеш" in out
    assert "Решение: call" in out
    assert "100,0%" in out
    assert "колл" in out


def test_cli_rejects_bad_cards(capsys):
    code = main(["--hero", "AxKh", "--villain", "QQ", "--pot", "10", "--to-call", "0"])
    err = capsys.readouterr().err
    assert code == 2
    assert err
```

- [ ] **Step 2: Убедиться, что тест падает**

```powershell
.\.venv\Scripts\python -m pytest tests/test_cli.py -v
```

Ожидание: FAIL, модуль `cli` не найден.

- [ ] **Step 3: Реализация**

`argparse`. `--hero` и `--villain` обязательны. `--board` по умолчанию `""`. `--pot` и `--to-call` — `int`. `--trials` по умолчанию 10000, `--seed` по умолчанию 0. Собрать отчёт, напечатать пять строк и абзац. Исключение `ValueError` — stderr и код 2. Прочие исключения нарратора поймать только вокруг `narrate`.

- [ ] **Step 4: Тест зелёный и ручной прогон**

```powershell
.\.venv\Scripts\python -m pytest tests/test_cli.py -v
.\.venv\Scripts\python -m poker_handline.cli --hero AhKh --board "Qh Jh Th 2c 3d" --villain 2d2s --pot 100 --to-call 50
```

Ожидание: pytest PASS, в консоли решение `call` и эквити `100,0%`.

- [ ] **Step 5: Commit**

```powershell
git add src/poker_handline/cli.py tests/test_cli.py
git commit -m "feat: add a CLI for one-hand analysis"
```

На этом фаза 1 готова. Прогон всего набора:

```powershell
.\.venv\Scripts\python -m pytest -v
```

Ожидание: PASS. Дальше фаза 2.

---

## Фаза 2. Локальное приложение

Одна страница. Поля: герой, борд, диапазон или рука злодея, банк, колл. Кнопка «Разобрать» вызывает `POST /api/analyze` и показывает те же строки, что CLI, плюс абзац. Отдельного фронтенд-сборщика нет: `index.html` лежит в пакете и отдаётся FastAPI.

### Task 10: HTTP API

**Files:**
- Create: `src/poker_handline/api.py`
- Create: `tests/test_api.py`

**Interfaces:**
- Consumes: `build_report`, `TemplateNarrator`
- Produces: `create_app() -> FastAPI`, маршрут `POST /api/analyze`

Тело запроса:

```json
{"hero": "AhKh", "board": "Qh Jh Th 2c 3d", "villain": "2d2s", "pot": 100, "to_call": 50}
```

Ответ 200:

```json
{
  "hand_name": "роял-флеш",
  "equity_share": 1.0,
  "required_equity": 0.3333333333333333,
  "action": "call",
  "method": "exact",
  "narration": "роял-флеш. Эквити против 2d2s: 100,0%. Для колла нужно 33,3%. Решение движка: колл.\nДвижок не оценивает фолд-эквити рейза и выбирает только колл или фолд."
}
```

Мусорные карты — 400 и `{"error": "<текст ValueError>"}`. В фазе 2 нарратор только шаблонный: страница не зависит от ключа.

- [ ] **Step 1: Тест через `TestClient`**

```python
from fastapi.testclient import TestClient

from poker_handline.api import create_app


def test_analyze_royal_flush():
    client = TestClient(create_app())
    response = client.post(
        "/api/analyze",
        json={"hero": "AhKh", "board": "Qh Jh Th 2c 3d", "villain": "2d2s", "pot": 100, "to_call": 50},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["hand_name"] == "роял-флеш"
    assert body["action"] == "call"
    assert body["equity_share"] == 1.0
    assert body["required_equity"] == 50 / 150
    assert "100,0%" in body["narration"]
    assert "колл" in body["narration"]


def test_analyze_rejects_bad_cards():
    client = TestClient(create_app())
    response = client.post(
        "/api/analyze",
        json={"hero": "Ax", "board": "", "villain": "QQ", "pot": 10, "to_call": 0},
    )
    assert response.status_code == 400
    assert response.json()["error"]
```

- [ ] **Step 2: Запустить и увидеть FAIL**

```powershell
.\.venv\Scripts\python -m pytest tests/test_api.py -v
```

- [ ] **Step 3: `create_app` с одним POST**

Pydantic-модель входа. `ValueError` → 400. Импорт FastAPI внутри функции не прятать: зависимость объявлена в extra `app`.

- [ ] **Step 4: PASS**

```powershell
.\.venv\Scripts\python -m pytest tests/test_api.py -v
```

- [ ] **Step 5: Commit**

```powershell
git add src/poker_handline/api.py tests/test_api.py
git commit -m "feat: expose one-hand analysis over HTTP"
```

### Task 11: Страница

**Files:**
- Create: `src/poker_handline/web/index.html`
- Modify: `src/poker_handline/api.py` (`GET /` отдаёт файл)
- Modify: `tests/test_api.py`

**Interfaces:**
- Consumes: `POST /api/analyze`
- Produces: форма, которую можно открыть на `http://127.0.0.1:8000`

- [ ] **Step 1: Тест, что `GET /` отдаёт форму**

```python
def test_index_has_the_form():
    client = TestClient(create_app())
    text = client.get("/").text
    for piece in ("hero", "board", "villain", "pot", "to_call", "/api/analyze", "Разобрать"):
        assert piece in text
```

Это защита от пустой страницы, не замена ручной проверки в браузере.

- [ ] **Step 2: FAIL, затем положить одну страницу**

`GET /` читает файл через `Path(__file__).parent / "web" / "index.html"`. Страница без сборщика: одна колонка, `max-width: 32rem`, поля с `name` ровно `hero`, `board`, `villain`, `pot`, `to_call`. Подписи: «Карты героя», «Борд», «Рука или диапазон оппонента», «Банк», «Колл». Кнопка «Разобрать». Результат — `<pre id="result">`. Плейсхолдер героя — `AhKh`. Скрипт делает `fetch("/api/analyze")`. На 400 пишет `error` в `#result` и не оставляет предыдущий успешный текст. На 200 пишет строки руки, эквити, требования колла, решения и `narration`.

- [ ] **Step 3: Поднять сервер и пройти сценарий руками**

```powershell
.\.venv\Scripts\python -m uvicorn poker_handline.api:create_app --factory --host 127.0.0.1 --port 8000
```

В браузере:

1. Роял-флеш `AhKh` / `Qh Jh Th 2c 3d` / `2d2s` / банк 100 / колл 50 → решение call, эквити 100,0%.
2. Очистить борд, герой `AsAh`, злодей `KdKh`, колл 0 → действие check, в тексте нет рекомендации размера ставки.
3. Герой `Ax` → сообщение об ошибке, предыдущий успешный текст не остаётся как будто разбор удался.
4. Узкое окно ~390px: форма в одну колонку, кнопка доступна без горизонтального скролла страницы.

- [ ] **Step 4: Commit**

```powershell
git add src/poker_handline/web/index.html src/poker_handline/api.py tests/test_api.py
git commit -m "feat: add a local page for one-hand analysis"
```

---

## Фаза 3. Статистика сессии

Источник — список рук в JSON, не текст PokerStars. Импорт чужого формата истории — отдельная задача после того, как формулы сойдутся на своём JSON. Иначе ошибка парсера маскируется под ошибку стата.

### Контракт руки

```python
@dataclass(frozen=True)
class Action:
    street: Literal["preflop", "flop", "turn", "river"]
    actor: Literal["hero", "villain"]
    kind: Literal["fold", "check", "call", "bet", "raise"]
    amount_bb: float

@dataclass(frozen=True)
class SessionHand:
    hand_id: str
    position: Literal["UTG", "HJ", "CO", "BTN", "SB", "BB"]
    saw_flop: bool
    went_to_showdown: bool
    won_at_showdown: bool
    result_bb: float
    actions: tuple[Action, ...]
```

`won_at_showdown` может быть истинным только при `went_to_showdown`. `went_to_showdown` может быть истинным только при `saw_flop`. Иначе `ValueError` на загрузке.

### Определения статов

Считаются только действия героя. Возможность (opportunity) нужна там, где указано; деление на ноль даёт `null`, не ноль.

| Стат | Числитель | Знаменатель |
| --- | --- | --- |
| hands | число рук | — |
| vpip | префлоп героя есть `call` или `raise`, и это не одинокий чек в BB | hands |
| pfr | префлоп героя есть `raise` | hands |
| three_bet | префлоп у героя есть `raise`, и раньше в списке префлопа есть `raise` оппонента | руки, где раньше префлоп-рейз оппонента и у героя есть своё префлоп-действие (фолд — возможность, не 3bet) |
| af | постфлоп сумма `bet`+`raise` героя | постфлоп число `call` героя |
| cbet_flop | герой был последним префлоп-рейзером и на флопе его первое действие `bet` | герой был последним префлоп-рейзером, `saw_flop`, на флопе у героя есть действие |
| wtsd | `went_to_showdown` | `saw_flop` |
| wsd | `won_at_showdown` | `went_to_showdown` |
| net_bb | сумма `result_bb` | — |

VPIP не считает обязательный блайнд. В этой модели блайнд не действие: действие появляется, когда игрок сам вложился коллом или рейзом. Лимп — это `call`.

### Task 12: Калькулятор

**Files:**
- Create: `src/poker_handline/stats.py`
- Create: `tests/test_stats.py`
- Create: `tests/fixtures/session_six_hands.json`

**Interfaces:**
- Consumes: нет, модуль не импортирует `equity`
- Produces: `parse_hand(data: dict) -> SessionHand`, `load_session(path) -> tuple[SessionHand, ...]`, `summarize(hands) -> dict[str, float | int | None]`

Шесть рук фикстуры и что они дают в числитель:

1. `h1` BTN, префлоп-рейз героя, флопа нет, `result_bb=1.5`. VPIP да, PFR да. 3bet-возможности нет. CBet нет: флопа нет.
2. `h2` BB, префлоп чек и флоп чек, `result_bb=0`. VPIP нет, PFR нет. Флоп видел.
3. `h3` CO, оппонент рейз, герой колл, на флопе герой колл, вскрытие и проигрыш, `result_bb=-5`. VPIP да, PFR нет. 3bet-возможность есть, 3bet нет. Постфлоп-колл для AF. WTSD да, W$SD нет.
4. `h4` BTN, рейз героя, колл оппонента, флоп-бет героя, `result_bb=6`. VPIP, PFR, CBet да. Постфлоп-бет для AF.
5. `h5` BTN, рейз героя, колл оппонента, флоп-чек героя, `result_bb=-2`. Возможность CBet есть, бет нет.
6. `h6` HJ, рейз оппонента, рейз героя, флопа нет, `result_bb=4`. VPIP, PFR, 3bet да.

Итог, его и утверждает тест: `hands == 6`, `vpip == 5/6`, `pfr == 4/6`, `three_bet == 1/2`, `af == 1.0`, `cbet_flop == 1/2`, `wtsd == 1/4`, `wsd == 0.0`, `net_bb == 4.5`.

- [ ] **Step 1: Фикстура и падающий тест**

`tests/fixtures/session_six_hands.json` — JSON-массив этих шести рук. У каждого действия поля `street`, `actor`, `kind`, `amount_bb`. Суммы: рейз открытия `2.5`, колл `2.5`, флоп-бет и флоп-колл в `h3`/`h4` по `3.0`, 3bet в `h6` — `8.0`, чеки — `0`.

```python
import pytest

from poker_handline.stats import load_session, parse_hand, summarize


def test_six_hand_fixture_matches_the_manual_tally():
    hands = load_session("tests/fixtures/session_six_hands.json")
    assert summarize(hands) == {
        "hands": 6,
        "vpip": 5 / 6,
        "pfr": 4 / 6,
        "three_bet": 1 / 2,
        "af": 1.0,
        "cbet_flop": 1 / 2,
        "wtsd": 1 / 4,
        "wsd": 0.0,
        "net_bb": 4.5,
    }


def test_showdown_flag_without_flop_is_rejected():
    with pytest.raises(ValueError):
        parse_hand(
            {
                "hand_id": "bad",
                "position": "BTN",
                "saw_flop": False,
                "went_to_showdown": True,
                "won_at_showdown": False,
                "result_bb": 0,
                "actions": [],
            }
        )
```

- [ ] **Step 2: Реализация `summarize` ровно по таблице определений**

Не добавлять «похожие» статы (steal, fold to cbet), пока на них нет строки в таблице и руки в фикстуре.

- [ ] **Step 3: PASS и commit**

```powershell
.\.venv\Scripts\python -m pytest tests/test_stats.py -v
git add src/poker_handline/stats.py tests/test_stats.py tests/fixtures/session_six_hands.json
git commit -m "feat: summarize a session of structured hands"
```

### Task 13: Разрез по позиции

**Files:**
- Modify: `src/poker_handline/stats.py`
- Modify: `tests/test_stats.py`

**Interfaces:**
- Produces: `summarize_by_position(hands) -> dict[str, dict]`

Ключи — только позиции, которые встретились. Внутри тот же словарь, что у `summarize`.

- [ ] **Step 1: Тест на той же фикстуре**

```python
def test_button_and_big_blind_slices():
    hands = load_session("tests/fixtures/session_six_hands.json")
    by_pos = summarize_by_position(hands)
    assert by_pos["BTN"]["hands"] == 3
    assert by_pos["BB"]["vpip"] == 0.0
    assert set(by_pos) == {"BTN", "BB", "CO", "HJ"}
```

- [ ] **Step 2: Реализация группирует руки по `position` и вызывает `summarize`**

- [ ] **Step 3: PASS и commit**

```powershell
.\.venv\Scripts\python -m pytest tests/test_stats.py -v
git add src/poker_handline/stats.py tests/test_stats.py
git commit -m "feat: split session stats by position"
```

---

## Фаза 4. Текст по статистике

Учебные коридоры для 6-max кэша, не GTO и не обещание винрейта. Они зашиты константой `BANDS` в `session_narrate.py`:

| Стат | Нижняя | Верхняя |
| --- | --- | --- |
| vpip | 0.22 | 0.28 |
| pfr | 0.18 | 0.23 |
| wtsd | 0.24 | 0.30 |
| wsd | 0.50 | 0.56 |
| cbet_flop | 0.60 | 0.75 |

Отдельно: если `vpip - pfr > 0.08`, пометка `vpip_pfr_gap`. Стат со значением `null` не сравнивается с коридором.

### Task 14: Шаблон сессии и проверка LLM

**Files:**
- Create: `src/poker_handline/session_narrate.py`
- Create: `tests/test_session_narrate.py`
- Modify: `src/poker_handline/cli.py`
- Modify: `tests/test_cli.py`

**Interfaces:**
- Consumes: словарь `summarize`
- Produces: `narrate_session(summary) -> str`, `LLMSessionNarrator.narrate(summary: dict) -> str`

Доли `vpip`, `pfr`, `three_bet`, `cbet_flop`, `wtsd`, `wsd` печатаются процентом с одним знаком и запятой. `hands` — целое. `af` — отношение с одним знаком (`1,0`), при `null` строка `AF: нет`. `net_bb` — число бб с одним знаком (`4,5`). Список статов включает WTSD. Под списком — только выход за коридор. У фикстуры `WTSD 25,0%` внутри `24–30`, поэтому строк `WTSD 25,0% выше` и `WTSD 25,0% ниже` нет. Строки выхода за коридор такие:

```text
VPIP 83,3% выше учебного коридора 22–28%.
PFR 66,7% выше учебного коридора 18–23%.
W$SD 0,0% ниже учебного коридора 50–56%.
CBet флоп 50,0% ниже учебного коридора 60–75%.
Разрыв VPIP и PFR больше 8%.
```

`83,3` — это `5/6`, `66,7` — это `4/6`, оба через формат `.1f`.

- [ ] **Step 1: Падающий тест шаблона и отказа LLM**

```python
import json

import httpx
import pytest

from poker_handline.session_narrate import LLMSessionNarrator, narrate_session
from poker_handline.stats import load_session, summarize


def test_template_flags_only_the_bands_this_fixture_misses():
    text = narrate_session(summarize(load_session("tests/fixtures/session_six_hands.json")))
    for line in (
        "VPIP 83,3% выше учебного коридора 22–28%.",
        "PFR 66,7% выше учебного коридора 18–23%.",
        "W$SD 0,0% ниже учебного коридора 50–56%.",
        "CBet флоп 50,0% ниже учебного коридора 60–75%.",
        "Разрыв VPIP и PFR больше 8%.",
    ):
        assert line in text
    assert "WTSD 25,0% выше" not in text
    assert "WTSD 25,0% ниже" not in text


def test_llm_session_narrator_must_quote_vpip():
    summary = summarize(load_session("tests/fixtures/session_six_hands.json"))

    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        assert "Не пересчитывай проценты" in body["messages"][0]["content"]
        return httpx.Response(200, json={"choices": [{"message": {"content": "Сессия нормальная."}}]})

    narrator = LLMSessionNarrator(
        "http://llm.test/v1", "test-key", "test-model", transport=httpx.MockTransport(handler)
    )
    with pytest.raises(ValueError):
        narrator.narrate(summary)
```

Проверка цитаты у `LLMSessionNarrator`: в ответе есть `83,3%`. Иначе `ValueError`. System-промпт содержит фразу `Не пересчитывай проценты`. Откат на шаблон делает CLI, не этот класс.

Вторая команда, отдельно от разбора руки:

```powershell
python -m poker_handline.cli session tests/fixtures/session_six_hands.json
```

`main(["session", "tests/fixtures/session_six_hands.json"])` печатает сводку и абзац, код 0. Тест в `tests/test_cli.py` проверяет, что в stdout есть `VPIP 83,3%` и нет похода в сеть.

---

## Что сознательно не входит ни в одну фазу

- Рейз, сайзинг, фолд-эквити, солверные деревья.
- Мультивей-эквити и сайд-поты.
- ICM, турнирные выплаты, анте.
- Захват экрана стола и совет во время раздачи в руме.
- Импорт PokerStars / GG. Сначала свой JSON и верные формулы.
- База данных. Шесть рук и любая сессия фазы 3 — файл.
- Веса комбинаций в диапазоне (`AA:0.5`).

## Проверка плана

Покрытие ответов: NLHE-движок — задачи 2–6. Одна раздача и текст — задачи 7–9. Приложение — задачи 10–11. Статистика — задачи 12–13. Агент по статистике — задача 14.

Дыры, которые легко принять за баг при реализации:

- Две карманные карты не оцениваются `rank_five`. Для них есть `hole_name`.
- Флоп и тёрн считаются перебором, префлоп — монте-Карло. Контрольный тёрн — `8h7h` против `QcQd` на `Ah Kh 2c 3d`: ровно `9/44`, не «около 20%» и не флеш-дро против сета.
- `pot` уже содержит ставку оппонента. Иначе требуемая эквити разъедется вдвое.
- Нарратор, который подменил «колл» на «рейз», — ошибка, а не стиль модели.
