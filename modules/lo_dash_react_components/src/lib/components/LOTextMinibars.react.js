/* Create a mini-bar-graph showing rhythm of text. Each bar represents
 * the length of one sentences, and each group of bars, one paragraph.
 *
 * It's not clear if this is an MVP yet; sentences should be stacked
 * bars (showing words), and sections should be clearly indicated.
 *
 * We'll also want to figure out how to handle multiple student texts
 * on one page, and in particular, axes and scaling.
 */

import * as React from 'react';
import './style.css';
import PropTypes from "prop-types";

import { BarChart, Bar, Cell, XAxis, YAxis, CartesianGrid, Tooltip } from 'recharts';

const sample_text = "Why Dogs are the Best Pets? \n\nWhen it comes to having a pet, there is no doubt that dogs are the best companion. There are a lot of reasons to support that statement. Dogs are loyal, friendly, and protective towards their owner. They are also great for physical activities and can be trained to perform various tasks. These are just a few reasons why dogs are the best pets for anyone.\n\nFirstly, dogs are known to be the most loyal pets. They are always by your side, wagging their tails, and giving you cuddles and kisses. No matter how bad your day is going, a dog’s unwavering loyalty makes the world seem that little bit brighter. This level of devotion is hard to find in any other animal. \n\nMoreover, dogs are very friendly and can bring so much joy to anyone’s life. They love meeting new people and make great companions even to strangers. They have an infectious and playful energy that always lifts your mood. That’s why they are also a great choice for families with children. They can help kids learn about responsibility, compassion, and friendship.\n\nAside from being great company, dogs also have a unique way of protecting their owners. They have a heightened sense of recognition when it comes to sensing danger or any suspicious activity. When they sense something amiss, they bark to alarm and protect their owner. A dog’s protective nature is an excellent asset to have, especially for elderly people living alone.\n\nLastly, dogs are very active and can keep their owners physically active too. Whether it's going for a walk or jog, playing fetch or joining their owner on hikes, dogs will make sure that their owner never gets bored. They can also be trained to perform various tasks like hunting, herding, police work, and search and rescue. These abilities show the intelligence and versatility of dogs as animals.\n\nIn conclusion, dogs are the best kind of pets for several reasons. They are loyal, friendly, and protective towards their owners that provide companionship, joy, and safety. They also have a unique ability to keep you active and are adaptable to perform various tasks. These positive qualities make dogs an excellent choice for anyone who wants a pet.\n"

// Split the text based on newlines or multiple newlines
function segmentTextIntoParagraphs(text) {
  return text.split(/\n+/).filter(paragraph => paragraph.trim() !== "");
}

// Split the text based on newlines or multiple newlines
function segmentParagraph(paragraph) {
  // Regular expression to match sentence-ending punctuation
  const sentenceEnd = /[.?!]/g;
  return paragraph.split(sentenceEnd).filter(Boolean).map(s => s.trim());
}

function segmentParagraphsIntoSentences(paragraphs) {
  // Map the segmentParagraph function over each paragraph
  return paragraphs.map(segmentParagraph);
}

// Count the number of words in a sentence
function countWords(text) {
  return text.split(/\s+/).length;
}

// Apply the word count function to each sentence in a list of paragraphs, each consisting of a list of sentences
function applyWordCount(paragraph_list) {
  return paragraph_list.map((sentences) => sentences.map((sentence) => countWords(sentence)))
}

/**
 * Annotates each sentence in a list of paragraphs with its corresponding word count.
 *
 * @param {Array} list - A list of paragraphs, where each paragraph is a list of sentences.
 *
 * @returns {Array} A list of paragraphs, where each paragraph is a list of objects representing sentences.
 * Each object has two properties: 'text' (the sentence text) and 'count' (the number of words in the sentence).
 *
 * @example
 *
 * const paragraphs = [['This is the first sentence.', 'This is the second sentence.'], ['Another paragraph with one sentence.']];
 * const annotatedParagraphs = annotateWithWordCount(paragraphs);
 * // annotatedParagraphs is now:
 * // [
 * //   [
 * //     { text: 'This is the first sentence.', count: 5 },
 * //     { text: 'This is the second sentence.', count: 5 }
 * //   ],
 * //   [
 * //     { text: 'Another paragraph with one sentence.', count: 5 }
 * //   ]
 * // ]
 */
function annotateWithWordCount(list) {
  return list.map((sentences) => 
    sentences.map((sentence) => ( {
      text: sentence,
      count: countWords(sentence)
    }))
  )
}

/**
 * A component that renders a miniature bar graph representation of text, where each bar represents a sentence, and each
 * set of bars, a paragraph
 */
class TextMiniGraph extends React.Component {
  /**
   * Prepares the chart data from the given text and yscale value
   * @param {string} text - The input text
   * @param {number} [yscale] - The scaling factor for the y-axis. This is used if there are multiple graphs on the same page (optional)
   * @returns {object[]} The chart data, an array of objects with properties: name, value, group, fill
   */
   static propTypes = {
    text: PropTypes.string.isRequired,
    height: PropTypes.number,
    width: PropTypes.number,
    yscale: PropTypes.number,
  };

  prepareChartData = (text, yscale) => {
    const annotatedTextLength = annotateWithWordCount(segmentParagraphsIntoSentences(segmentTextIntoParagraphs(text)));
    const angleGoldenRatio = 137.5;
    const ratioColor = index => `hsl(${(index * angleGoldenRatio) % 360}, 75%, 75%)`;
    let chartData = annotatedTextLength.flatMap((array, index) => [
      ...array.map(value => ({ name:value.text, value: value.count, group: index, fill: ratioColor(index) })),
      { value: 0, group: -1 }
    ]).slice(0, -1);
    return chartData;
  }

  render() {
    const { text, height = 60, width = 200, yscale = null } = this.props;
    const chartData = this.prepareChartData(text, yscale);
    return (
      <BarChart height={height} width={width} data={chartData}>
        <Tooltip content={props => props.label } />
        <Bar dataKey="value">
          {
            chartData.map((entry, index) => (
              <Cell key={`cell-${index}`} stroke={entry.fill} fill={entry.fill}/>
            ))
          }
        </Bar>
      </BarChart>
    );
  }
}

export default function App() {
  return (
    <div>
      <TextMiniGraph text={sample_text} height={60} width={200} />
    </div>
  );
}
