#!/usr/bin/env python3
"""기출변형 예문(재작성)+해석을 basic-day1에 병합. 출처(src)는 assigned.json에서 가져와 정합성 보장."""
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
assigned = json.load(open(ROOT/"corpus"/"assigned.json"))

# word -> (기출변형 예문, 해석)  ※ 실제 기출 문장을 CEFR B1~B2로 재작성(그대로 복제 금지)
EX = {
 "public":("Good tourism can improve the roads and public facilities that local residents use.",
           "좋은 관광은 지역 주민이 이용하는 도로와 공공시설을 개선할 수 있다."),
 "form":("The artist’s sculptures show the human form in a completely new way.",
         "그 예술가의 조각은 인간의 형태를 완전히 새로운 방식으로 보여 준다."),
 "provide":("Your new membership provides special discounts at the museum.",
            "새 회원권은 박물관에서 특별 할인을 제공한다."),
 "various":("Students remember a concept better when they meet it in various contexts.",
            "학생들은 다양한 맥락에서 그 개념을 접할 때 더 잘 기억한다."),
 "behavior":("Under stress, people often show behavior that is unlike their usual selves.",
             "스트레스를 받으면 사람들은 흔히 평소 자신과 다른 행동을 보인다."),
 "nature":("Many advertisements link their products to an image of nature.",
           "많은 광고가 자사 제품을 자연의 이미지와 연결한다."),
 "reason":("A strong vision motivates workers for the same reason a great goal inspires us.",
           "강력한 비전은 위대한 목표가 우리를 고무하는 것과 같은 이유로 직원들에게 동기를 부여한다."),
 "tend":("Information from distant contacts tends to be weak but to reach far.",
         "먼 인맥에서 오는 정보는 약하지만 멀리까지 닿는 경향이 있다."),
 "value":("The value of a forest can differ greatly from one group of people to another.",
          "숲의 가치는 집단에 따라 크게 다를 수 있다."),
 "role":("The power of suggestion plays a key role in shaping people’s decisions.",
         "암시의 힘은 사람들의 결정을 형성하는 데 핵심적인 역할을 한다."),
 "research":("Research shows that children do better in math when music is part of the lesson.",
             "연구에 따르면 아이들은 수업에 음악이 포함될 때 수학을 더 잘한다."),
 "personal":("He says that two personal letters completely changed his life.",
             "그는 두 통의 개인적인 편지가 자기 삶을 완전히 바꿔 놓았다고 말한다."),
 "develop":("Later in his career, he developed his own theory of social systems.",
            "경력 후반에 그는 자신만의 사회 체계 이론을 발전시켰다."),
 "future":("The doctor of the future will need to treat each patient differently.",
           "미래의 의사는 환자마다 다르게 치료해야 할 것이다."),
 "skill":("Praise alone will not help you develop real tennis skills.",
          "칭찬만으로는 실제 테니스 실력을 기르는 데 도움이 되지 않는다."),
 "attention":("When you are under pressure, pay more attention to rest and relaxation.",
              "압박을 받을 때는 휴식과 이완에 더 많은 주의를 기울여라."),
 "century":("In the twentieth century, advances in technology changed how we store food.",
            "20세기에 기술의 발전은 우리가 음식을 저장하는 방식을 바꾸었다."),
 "modern":("Modern economies depend on moving goods and people safely and reliably.",
           "현대 경제는 상품과 사람을 안전하고 확실하게 이동시키는 데 의존한다."),
 "control":("A good leader never lets anger get out of control.",
            "훌륭한 리더는 결코 분노가 통제를 벗어나게 두지 않는다."),
 "particular":("Early humans in Europe hunted large animals, particularly reindeer.",
               "유럽의 초기 인류는 큰 동물, 특히 순록을 사냥했다."),
 "society":("Even when an idea fits a society’s needs, it may not be accepted.",
            "어떤 생각이 사회의 필요에 부합하더라도 받아들여지지 않을 수 있다."),
 "effect":("Scientists asked what effect the warming had on Alaska’s glaciers.",
           "과학자들은 그 온난화가 알래스카의 빙하에 어떤 영향을 미쳤는지 물었다."),
 "certain":("Some thinkers assume that certain works of art produce certain effects.",
            "어떤 사상가들은 특정 예술 작품이 특정한 효과를 낳는다고 가정한다."),
 "physical":("A metaphor makes us think about the physical qualities of an object.",
             "은유는 우리가 어떤 사물의 물리적 특성을 생각하게 만든다."),
 "science":("Decades later, science finally faced the questions Mendel had raised.",
            "수십 년 후, 과학은 마침내 멘델이 제기한 질문들에 직면했다."),
 "knowledge":("The best tests probe a student’s knowledge at a deep level.",
              "가장 좋은 시험은 학생의 지식을 깊은 수준에서 점검한다."),
 "culture":("In most musical cultures around the world, pitch plays a central role.",
            "전 세계 대부분의 음악 문화에서 음높이는 중심적인 역할을 한다."),
 "believe":("Greene believes that emotions act as the automatic setting for our morality.",
            "그린은 감정이 우리 도덕의 자동 설정 역할을 한다고 믿는다."),
 "company":("One company developed a shared ‘technology shelf’ for its engineers.",
            "한 회사는 엔지니어들을 위한 공용 ‘기술 선반’을 개발했다."),
 "create":("The very features that create expertise in one field can cause blindness in others.",
           "한 분야에서 전문성을 만들어 내는 바로 그 특성이 다른 분야에서는 무지를 낳을 수 있다."),
 "system":("When the economy works as a belief system, it limits a consumer’s free choice.",
           "경제가 신념 체계로 작동하면 소비자의 자유로운 선택을 제한한다."),
 "activity":("Choosing how to frame a problem is a critical activity in solving it.",
             "문제를 어떻게 규정할지 정하는 것은 문제 해결에서 매우 중요한 활동이다."),
 "require":("A careful defense is required against any weak argument.",
            "어떤 허술한 주장에 대해서도 신중한 방어가 요구된다."),
 "affect":("Dogs are not affected by outside events the way humans are.",
           "개는 인간과 달리 외부 사건에 영향을 받지 않는다."),
 "increase":("Rising incomes usually lead to an increase in car ownership.",
             "소득 증가는 보통 자동차 소유의 증가로 이어진다."),
 "reduce":("To feel happier, we can reduce the number of things we try to achieve.",
           "더 행복해지기 위해 우리는 이루려는 일의 수를 줄일 수 있다."),
 "improve":("Sharing food greatly improves each bat’s chances of survival.",
            "먹이를 나누는 것은 각 박쥐의 생존 가능성을 크게 향상시킨다."),
 "social":("No social institution can be fully understood on its own.",
           "어떤 사회 제도도 그 자체만으로는 완전히 이해될 수 없다."),
 "individual":("Some scholars argue that the ‘individual’ is partly a social invention.",
               "일부 학자들은 ‘개인’이 부분적으로 사회적 발명품이라고 주장한다."),
 "environment":("To understand the frog, watch it swim and consider its environment.",
                "개구리를 이해하려면 그것이 헤엄치는 모습을 보고 그 환경을 고려하라."),
}

book = json.load(open(ROOT/"suneung-basic-day1.json"))
miss=[]
for w in book["words"]:
    en=w["en"]
    if en not in EX or en not in assigned:
        miss.append(en); continue
    ex,tr = EX[en]
    a = assigned[en]
    m0 = w["meanings"][0]
    m0["ex"]=ex; m0["tr"]=tr
    m0["src"]=f"{a['label']} {a['item']}번"
book["exampleNote"]="예문은 실제 기출 지문(연도·회차·문항 표기)을 CEFR 수준에 맞춰 재작성한 기출변형입니다."
json.dump(book, open(ROOT/"suneung-basic-day1.json","w"), ensure_ascii=False, indent=1)
print("merged. missing:", miss)
print("샘플:", json.dumps(book["words"][0]["meanings"][0], ensure_ascii=False))
