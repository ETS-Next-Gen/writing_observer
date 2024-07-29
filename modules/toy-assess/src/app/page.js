'use client';
// @refresh reset

import { TextInput, NavigateButton, ResetButton, LLMFeedback, LLMButton, LLMPrompt, Variable, Element, StoreVariable, List, SideBarPanel, MainPane, ShowComponentButton, HideableComponent } from './components.js';


export default function Home() {
  return (
    <>
      <h1> Pages </h1>
      <p> We have many more than committed here, including math problems, SBAs, etc. We are leaving one demo for now, since the rest are externally contributed and may have IP issues. </p>
      <ul>
        <li><a href="/changer/">Text style changer demo</a></li>
      </ul>
    </>
  );
}
