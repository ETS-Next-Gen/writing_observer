'''
This is an interface to a variety of sample texts to play with.
'''

from enum import Enum
import json
import os
import os.path
import random

import loremipsum
import wikipedia


TextTypes = Enum('TextTypes', [
    "SHORT_STORY", "ARGUMENTATIVE", "LOREM", "WIKI_SCIENCE", "WIKI_HISTORY"
])


def sample_texts(text_type=TextTypes.LOREM, count=1):
    '''
    Returns a sample, random essay of the appropriate type
    '''
    if text_type == TextTypes.LOREM:
        return [lorem() for x in range(count)]

    sources = {
        TextTypes.ARGUMENTATIVE: ARGUMENTATIVE_ESSAYS,
        TextTypes.SHORT_STORY: SHORT_STORIES,
        TextTypes.WIKI_SCIENCE: WIKIPEDIA_SCIENCE,
        TextTypes.WIKI_HISTORY: WIKIPEDIA_HISTORY
    }

    source = sources[text_type]

    essays = []
    while count > len(source):
        essays.extend(source)
        count = count - len(source)

    essays.extend(random.sample(source, count))

    if text_type in [TextTypes.WIKI_SCIENCE, TextTypes.WIKI_HISTORY]:
        essays = map(wikitext, essays)

    return [e.strip() for e in essays]


def lorem(paragraphs=5):
    '''
    Generate lorem ipsum test text.
    '''
    return "\n\n".join(loremipsum.get_paragraphs(paragraphs))


CACHE_PATH = os.path.join(os.path.dirname(__file__), "data")


def wikitext(topic):
    if not os.path.exists(CACHE_PATH):
        os.mkdir(CACHE_PATH)
    cache_file = os.path.join(CACHE_PATH, f"{topic}.json")

    if not os.path.exists(cache_file):
        page = wikipedia.page(topic)
        data = {
            "content": page.content,
            "summary": page.summary,
            "title": page.title,
            "rev": page.revision_id,
            "url": page.url,
            "id": page.pageid
        }
        with open(cache_file, "w") as fp:
            json.dump(data, fp, indent=3)

    with open(cache_file) as fp:
        data = json.load(fp)

    return data["content"]


# Wikipedia topics
WIKIPEDIA_SCIENCE = [
    "Corona_Borealis", "Funerary_art", "Splendid_fairywren", "European_hare", "Exelon_Pavilions", "Northern_rosella"
]

WIKIPEDIA_HISTORY = [
    "Gare_Montparnasse", "History_of_photography", "Cliff_Palace",
    "War_of_the_Fifth_Coalition", "Operation_Overlord",
    "Slavery_in_the_United_States", "Dust_Bowl", "The_Rhodes_Colossus"
]

# Short stories, from GPT-3
SHORT_STORIES = ["""The snail had always dreamed of going to space. It was a lifelong dream, and finally, the day had arrived. The snail was strapped into a rocket, and prepared for takeoff.

As the rocket blasted off, the snail felt a sense of exhilaration. It was finally achieving its dream! The snail looked out the window as the Earth got smaller and smaller. Soon, it was in the vastness of space, floating weightlessly.

The snail was content, knowing that it had finally accomplished its dream. It would never forget this moment, floating in space, looking at the stars.
""",
"""One day, an old man was sitting on his porch, telling jokes to his grandson. The grandson was laughing hysterically at every joke.

Suddenly, a spaceship landed in front of them. A alien got out and said, "I come in peace! I come from a planet of intelligent beings, and we have heard that humans are the most intelligent beings in the universe. We would like to test your intelligence."

The old man thought for a moment, then said, "Okay, I'll go first. What has two legs, but can't walk?"

The alien thought for a moment, then said, "I don't know."

The old man chuckled and said, "A chair."
""",
"""The boy loved dolls. He loved their soft skin, their pretty clothes, and the way they always smelled like roses. He wanted to be a doll himself, so he could be pretty and perfect like them.

One day, he found a doll maker who promised to make him into a doll. The boy was so excited, and couldn't wait to become a doll.

The doll maker kept her promise, and the boy became a doll. He was perfect in every way, and he loved it. He loved being pretty and perfect, and he loved the way everyone fussed over him and treated him like a delicate little thing.

The only problem was that the boy's soul was now trapped inside the doll's body, and he could never be human again.
""",
"""The mouse had been hunting the cat for days. It was a big cat, twice her size, with sharp claws and teeth. But the mouse was determined to catch it.

Finally, she corner the cat in an alley. The cat hissed and slashed at the mouse, but the mouse was quick. She dart to the side and bit the cat's tail.

The cat yowled in pain and fled, and the mouse triumphantly went home with her prize.
""",
"""When I was younger, I dreamt of scaling Mt. Everest. It was the tallest mountain in the world, and I wanted to conquer it.

But then I was in a car accident that left me paralyzed from the waist down. I was confined to a wheelchair, and my dreams of scaling Everest seemed impossible.

But I didn't give up. I trained my upper body to be stronger, and I developed a special wheelchair that could handle the rough terrain.

Finally, after years of preparation, I made it to the top of Everest. It was the hardest thing I'd ever done, but I did it. And it was the best feeling in the world.
""",
"""The cucumber and the salmon were both new to the tank. The cucumber was shy and withdrawn, while the salmon was outgoing and friendly.

The salmon swim over to the cucumber and said hi. The cucumber was surprised, but happy to have made a new friend.

The two of them became fast friends, and they loved spending time together. The salmon would swim around the cucumber, and the cucumber would wrap itself around the salmon. They were both happy to have found a friend in the other.
""",
"""
"I can't believe we're all going to different colleges," said Sarah.

"I know," said John. "It's going to be weird not seeing you guys every day."

"But it's not like we're never going to see each other again," said Jane. "We can still visit each other, and keep in touch."

"I'm going to miss you guys so much," said Sarah.

"We're going to miss you too," said John.

"But we'll always be friends," said Jane.
""",
"""
The Polish winged hussars were a fearsome group of knights who rode into battle on horseback, armed with lances and swords. They were known for their skill in combat and their ability to move quickly and efficiently across the battlefield. The samurai were a similar group of warriors from Japan who were also highly skilled in combat and known for their speed and accuracy.

One day, a group of samurai were travelling through Poland when they came across a group of winged hussars. The two groups immediately began to battle, and it quickly became clear that the hussars had the upper hand. The samurai were outnumbered and outmatched, and they were soon defeated.

As the hussars celebrated their victory, one of the samurai walked up to them and bowed. The hussars were surprised by this gesture, and one of them asked the samurai why he had bowed.

The samurai explained that in his culture, it was customary to bow to one's enemies after a battle. He said that the hussars had fought with honor and skill, and that they deserved his respect.

The hussars were touched by the samurai's words, and they returned the gesture. From then on, the two groups became friends, and they often fought side by side against their common enemies.
"""
]

# Argumentative essays, from GPT-3
ARGUMENTATIVE_ESSAYS = [
"""
Joe Biden has been in the public eye for over 40 years, and during that time he has shown himself to be a competent and trustworthy leader. He has served as a U.S. Senator from Delaware, and as the Vice President of the United States. In both of these roles, he has demonstrated his commitment to making the lives of Americans better.

Joe Biden has a long history of fighting for the middle class. He was a key player in the creation of the Affordable Care Act, which has helped millions of Americans get access to quality healthcare. He also helped to pass the American Recovery and Reinvestment Act, which provided a much-needed boost to the economy during the Great Recession.

Joe Biden is also a strong supporter of gun reform. After the tragic shooting at Sandy Hook Elementary School, he led the charge for background checks and other common-sense gun laws. He knows that we need to do more to keep our children safe from gun violence, and he will continue to fight for gun reform as president.

Joe Biden is the right choice for president because he has the experience and the track record to get things done. He has shown that he cares about the American people, and he will fight for the middle class.
""",
"""Donald Trump is a successful businessman and television personality who has been in the public eye for over 30 years. He has a proven track record of getting things done, and he has the business acumen to get our economy back on track.

Trump is a strong supporter of the Second Amendment, and he has pledged to protect the right of Americans to bear arms. He also supports the use of stop-and-frisk tactics by police, which have been proven to be effective in reducing crime.

Trump is also a stron
HN isn't g supporter of law and order. He has pledged to increase funding for police departments, and he has vowed to crack down on crime in our inner cities. Trump knows that we need to keep our communities safe, and he will make sure that our laws are enforced.

Trump is the right choice for president because he has the experience and the leadership to get things done. He has shown that he cares about the American people, and he will fight for our safety and our economic success.
""",
"""The sun orbits the earth. This can be proven by the fact that the sun rises in the east and sets in the west. If the earth was orbiting the sun, then the sun would rise in the west and set in the east.

The sun also appears to be stationary in the sky, while the earth is spinning on its axis. If the sun was orbiting the earth, then it would appear to be moving across the sky.

There are also Biblical passages that support the idea that the sun orbits the earth. In the book of Joshua, the sun is said to stand still in the sky so that Joshua could win a battle. In the book of Psalms, the earth is said to be “established” on its foundations, and the sun is said to “move” around the earth.

The sun orbits the earth. This can be proven by the evidence from astronomy and the Bible. The sun orbits the earth, and this is the truth.
""",
"""The United States should invade Mexico. Mexico is a country that is rife with corruption and violence. The Mexican government is unable to control the drug cartels, and as a result, drug-related violence is out of control.

The drug cartels are also responsible for smuggling drugs into the United States. This has led to a rise in drug addiction and crime in the United States.

The Mexican government is also failing to protect its citizens from the cartels. In 2013, over 70,000 people were killed in drug-related violence in Mexico. This is an unacceptable level of violence, and the Mexican government is not doing enough to stop it.

The United States should invade Mexico in order to stop the drug-related violence and to protect the American people. Mexico is not doing enough to stop the cartels, and as a result, innocent people are being killed. The United States has a duty to protect its citizens, and invading Mexico is the best way to do that.
""",
"""The world is facing a population crisis. There are too many people on the planet, and resources are becoming scarce. We need to find a way to reduce the population, or else we will all suffer the consequences.

One way to reduce the population is to encourage people to have fewer children. Another way to reduce the population is to encourage people to live longer.

One way to encourage people to have fewer children is to offer financial incentives. For example, the government could offer a tax break to couples who have only one child. The government could also provide free childcare for couples who have two children or fewer.

Another way to encourage people to have fewer children is to make it more difficult for couples to have children. For example, the government could make it illegal for couples to have more than two children. The government could also make it more difficult for couples to get married if they already have children.

One way to encourage people to live longer is to offer financial incentives. For example, the government could offer a tax break to people who live to the age of 80. The government could also provide free healthcare for people who live to the age of 90.

We need to find a way to reduce the population, or else we will all suffer the consequences. Reducing the population is not an easy task, but it is something that we must do in order to save the planet.
""",
"""
The drinking age should be lowered. The current drinking age of 21 is not working. It has led to an increase in binge drinking among college students, and it has not stopped underage drinking.

The drinking age should be lowered to 18. This would align the drinking age with the age of majority, and it would allow adults to make their own decisions about drinking.

The drinking age should be lowered to 18 because it would make it easier for adults to supervise underage drinking. If the drinking age was 21, then adults would be less likely to intervene when they see underage drinking.

The drinking age should be lowered to 18 because it would allow adults to make their own decisions about drinking. Adults should be able to decide for themselves whether or not they want to drink.

The drinking age should be lowered to 18. The current drinking age is not working, and it is time for a change.
""",
"""The United States should elect the King of England as president because he has the experience and qualifications that are needed to lead the country. The King of England has a long history of ruling over a large and complex country, and he has the necessary skills to deal with the challenges that the US faces. In addition, the King of England is a highly respected world leader, and his election would be a strong statement to the rest of the world that the US is a serious country that is committed to democracy and the rule of law.""",
"""Public education should be eliminated, in favor of free labor camps.

Education is a fundamental human right. It is essential to the exercise of all other human rights and freedoms. It promotes individual and community development, and is essential to the advancement of societies.

However, public education is not free. It is expensive, and the cost is borne by taxpayers. In addition, public education is not effective. It is not meeting the needs of students, and it is not preparing them for the future.

Free labor camps would be a more effective and efficient way to educate children. Labor camps would provide children with the opportunity to learn valuable skills, while also providing them with a place to live and work.

Children in labor camps would not be subjected to the same overcrowded and underfunded classrooms that they are currently in. They would have the opportunity to learn in a more hands-on environment, and would be able to apply the skills they learned to real-world situations.

In addition, labor camps would provide children with the opportunity to earn a living. They would no longer be reliant on their parents or the government for financial support. They would be able to support themselves, and would be less likely to end up in poverty.
""",
"""As our population ages, it becomes increasingly important to find ways to keep seniors active and engaged in their communities. One way to do this is to require all seniors to serve a mandatory military duty.

There are many benefits to having seniors serve in the military. First, it would help to ease the burden on our overstretched military. With more seniors serving, we would not have to rely as heavily on young people to fill the ranks.

Second, seniors have a lot to offer the military. They are often more mature and level-headed than younger soldiers, and they can provide valuable experience and perspective.

Third, this would be a great way to get seniors more involved in their communities. They would have a sense of purpose and would be working together for a common goal.

There are some who may argue that seniors are not physically able to serve in the military. However, there are many ways to accommodate seniors of all physical abilities. For example, they could serve in administrative roles or be paired with younger soldiers to provide support and guidance.

Overall, requiring seniors to serve in the military would be a great way to keep them active and engaged in their communities. It would also be a valuable asset to our military.""",
"""It is time for our society to take a stand against the growing problem of preschool violence. Many people believe that the death penalty is too harsh of a punishment for young children, but I believe that it is necessary in order to send a clear message that violence will not be tolerated.

Preschools are supposed to be places of learning and growth, not places where children are afraid to go because of the threat of violence. Unfortunately, that is not the reality in many schools today. In the past year alone, there have been several reports of preschoolers being involved in fights and even bringing weapons to school.

This type of behavior cannot be tolerated. If we want to prevent violence in our schools, we need to send a clear message that it will not be tolerated. The best way to do this is to implement the death penalty at preschools.

Some people will argue that the death penalty is too harsh of a punishment for young children. However, I believe that it is necessary in order to send a clear message that violence will not be tolerated. If we do not take a stand now, the problem will only get worse.

Implementing the death penalty at preschools will send a clear message that violence will not be tolerated. It is time for our society to take a stand against the growing problem of preschool violence.
"""
]

GPT3_TEXTS = {
    'story': SHORT_STORIES,
    'argument': ARGUMENTATIVE_ESSAYS
}
