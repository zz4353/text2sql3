import json
from llm_client import OpenAIClient
from pipeline.extract_values import extract_values
from db_client import get_llm_table_schema_context, DB_ID

with open("test.json", encoding="utf-8") as f:
    test = json.load(f)

sample = test[0]

data = [
  {
    "table": "alignment",
    "operation": None,
    "records": [
      {
        "alignment": "Good"
      },
      {
        "alignment": "Bad"
      },
      {
        "alignment": "Neutral"
      }
    ]
  },
  {
    "table": "gender",
    "operation": None,
    "records": [
      {
        "gender": "Male"
      },
      {
        "gender": "Female"
      }
    ]
  },
  {
    "table": "superhero",
    "operation": None,
    "records": [
      {
        "superhero_name": "Captain Marvel",
        "gender_id": 1,
        "alignment_id": 1
      },
      {
        "superhero_name": "Mystique",
        "gender_id": 2,
        "alignment_id": 2
      },
      {
        "superhero_name": "Deadpool",
        "gender_id": 1,
        "alignment_id": 2
      },
      {
        "superhero_name": "Storm",
        "gender_id": 2,
        "alignment_id": 1
      },
      {
        "superhero_name": "Green Goblin",
        "gender_id": 1,
        "alignment_id": 2
      },
      {
        "superhero_name": "Wonder Woman",
        "gender_id": 2,
        "alignment_id": 1
      },
      {
        "superhero_name": "Hawkeye",
        "gender_id": 1,
        "alignment_id": 2
      },
      {
        "superhero_name": "Spider-Man",
        "gender_id": 1,
        "alignment_id": 1
      },
      {
        "superhero_name": "Harley Quinn",
        "gender_id": 2,
        "alignment_id": 2
      },
      {
        "superhero_name": "The Punisher",
        "gender_id": 1,
        "alignment_id": 2
      },
      {
        "superhero_name": "Black Widow",
        "gender_id": 2,
        "alignment_id": 1
      },
      {
        "superhero_name": "Thanos",
        "gender_id": 1,
        "alignment_id": 2
      },
      {
        "superhero_name": "Rogue",
        "gender_id": 2,
        "alignment_id": 1
      },
      {
        "superhero_name": "Loki",
        "gender_id": 1,
        "alignment_id": 2
      },
      {
        "superhero_name": "Batgirl",
        "gender_id": 2,
        "alignment_id": 1
      },
      {
        "superhero_name": "Magneto",
        "gender_id": 1,
        "alignment_id": 2
      },
      {
        "superhero_name": "Catwoman",
        "gender_id": 2,
        "alignment_id": 2
      },
      {
        "superhero_name": "Iron Man",
        "gender_id": 1,
        "alignment_id": 1
      },
      {
        "superhero_name": "Cheetah",
        "gender_id": 2,
        "alignment_id": 2
      },
      {
        "superhero_name": "Venom",
        "gender_id": 1,
        "alignment_id": 2
      },
      {
        "superhero_name": "She-Hulk",
        "gender_id": 2,
        "alignment_id": 1
      },
      {
        "superhero_name": "Doctor Doom",
        "gender_id": 1,
        "alignment_id": 2
      },
      {
        "superhero_name": "Jessica Jones",
        "gender_id": 2,
        "alignment_id": 1
      },
      {
        "superhero_name": "Ghost Rider",
        "gender_id": 1,
        "alignment_id": 2
      },
      {
        "superhero_name": "Wonder Girl",
        "gender_id": 2,
        "alignment_id": 1
      },
      {
        "superhero_name": "Bane",
        "gender_id": 1,
        "alignment_id": 2
      },
      {
        "superhero_name": "Raven",
        "gender_id": 2,
        "alignment_id": 2
      },
      {
        "superhero_name": "Captain America",
        "gender_id": 1,
        "alignment_id": 1
      },
      {
        "superhero_name": "Poison Ivy",
        "gender_id": 2,
        "alignment_id": 2
      },
      {
        "superhero_name": "The Riddler",
        "gender_id": 1,
        "alignment_id": 2
      },
      {
        "superhero_name": "Batwoman",
        "gender_id": 2,
        "alignment_id": 1
      },
      {
        "superhero_name": "Ultron",
        "gender_id": 1,
        "alignment_id": 2
      },
      {
        "superhero_name": "Enchantress",
        "gender_id": 2,
        "alignment_id": 2
      },
      {
        "superhero_name": "Green Lantern",
        "gender_id": 1,
        "alignment_id": 1
      },
      {
        "superhero_name": "Viper",
        "gender_id": 2,
        "alignment_id": 2
      },
      {
        "superhero_name": "Kraven the Hunter",
        "gender_id": 1,
        "alignment_id": 2
      },
      {
        "superhero_name": "Zatanna",
        "gender_id": 2,
        "alignment_id": 1
      },
      {
        "superhero_name": "Kingpin",
        "gender_id": 1,
        "alignment_id": 2
      },
      {
        "superhero_name": "Black Cat",
        "gender_id": 2,
        "alignment_id": 2
      },
      {
        "superhero_name": "Blue Beetle",
        "gender_id": 1,
        "alignment_id": 1
      },
      {
        "superhero_name": "Lady Deathstrike",
        "gender_id": 2,
        "alignment_id": 2
      },
      {
        "superhero_name": "Taskmaster",
        "gender_id": 1,
        "alignment_id": 2
      },
      {
        "superhero_name": "Misty Knight",
        "gender_id": 2,
        "alignment_id": 1
      },
      {
        "superhero_name": "Red Skull",
        "gender_id": 1,
        "alignment_id": 2
      },
      {
        "superhero_name": "Silver Sable",
        "gender_id": 2,
        "alignment_id": 2
      },
      {
        "superhero_name": "Nightwing",
        "gender_id": 1,
        "alignment_id": 1
      },
      {
        "superhero_name": "Enchantress",
        "gender_id": 2,
        "alignment_id": 2
      },
      {
        "superhero_name": "Bullseye",
        "gender_id": 1,
        "alignment_id": 2
      },
      {
        "superhero_name": "Oracle",
        "gender_id": 2,
        "alignment_id": 1
      },
      {
        "superhero_name": "Hobgoblin",
        "gender_id": 1,
        "alignment_id": 2
      },
      {
        "superhero_name": "Dazzler",
        "gender_id": 2,
        "alignment_id": 2
      },
      {
        "superhero_name": "Wolverine",
        "gender_id": 1,
        "alignment_id": 1
      },
      {
        "superhero_name": "Talia al Ghul",
        "gender_id": 2,
        "alignment_id": 2
      },
      {
        "superhero_name": "Deathstroke",
        "gender_id": 1,
        "alignment_id": 2
      },
      {
        "superhero_name": "Valkyrie",
        "gender_id": 2,
        "alignment_id": 1
      },
      {
        "superhero_name": "Sinestro",
        "gender_id": 1,
        "alignment_id": 2
      },
      {
        "superhero_name": "Misty Knight",
        "gender_id": 2,
        "alignment_id": 2
      }
    ]
  }
]

from pipeline.build_sqls import build_sqls

sqls = (build_sqls(DB_ID(sample['db_id']), data))
for sql in sqls:
    print(sql)
    print("----------------------")