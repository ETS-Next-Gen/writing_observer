//This setup uses model="gpt-3.5-turbo" & apiVersion="2023-05-15";

const { OpenAIClient, AzureKeyCredential } = require("@azure/openai");

const resource=await process.env.OPENAI_URL;
const deploymentID=process.env.OPENAI_DEPLOYMENT_ID;
const key = await process.env.OPENAI_API_KEY;

console.log("In azureInterface");
console.log("key: " + key);
const client = new OpenAIClient(resource, new AzureKeyCredential(key));
console.log("client created");

export async function listChatCompletions(
  messages,
  {
    maxTokens=128,
    temperature=0.8 // Currently ignored
  }) {
    console.log("azureInterface.listChatCompletions called")
    console.log(`Messages: ${messages.map((m) => m.content).join("\n")}`);
  
    const events = client.listChatCompletions(deploymentID, messages, { maxTokens });
    let response = "";
    for await (const event of events) {
      for (const choice of event.choices) {
        const delta = choice.delta?.content;
        if (delta !== undefined) {
            response = response + delta;
            console.log(`Chatbot: ${delta}`);
        }
      }
    }
    return response;
}
