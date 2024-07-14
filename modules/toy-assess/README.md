This is a [Next.js](https://nextjs.org/) project bootstrapped with [`create-next-app`](https://github.com/vercel/next.js/tree/canary/packages/create-next-app).

## Setup
If you haven't yet, run:
npm install next@latest

This may require also running
npm audit fix

You will also need to install writing_observer and package up lo_event to use inside the project.
Place to clone from: https://github.com/ETS-Next-Gen/writing_observer
cd to cloned directory, type npm install

Then, inside writing_observer/modules/lo_event:
npm install redux
npm install redux-thunk

Once you have writing observer setup, go back to the toysba directory and do something like the following:

npm install ../writing_observer/modules/lo_event
npm i @azure/openai@1.0.0-beta.7
npm install formdata-node

then set the following environment variables:
OPENAI_API_RESOURCE
OPENAI_DEPLOYMENT_ID
OPENAI_API_KEY

This assumes that writing_observer is installed in the same directory as toy-sba.

## Getting Started
First, run the development server:

```bash
npm run dev
# or
yarn dev
# or
pnpm dev
# or
bun dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

You can start editing the page by modifying `app/page.js`. The page auto-updates as you edit the file.

This project uses [`next/font`](https://nextjs.org/docs/basic-features/font-optimization) to automatically optimize and load Inter, a custom Google Font.

## Learn More

To learn more about Next.js, take a look at the following resources:

- [Next.js Documentation](https://nextjs.org/docs) - learn about Next.js features and API.
- [Learn Next.js](https://nextjs.org/learn) - an interactive Next.js tutorial.

You can check out [the Next.js GitHub repository](https://github.com/vercel/next.js/) - your feedback and contributions are welcome!

## Deploy on Vercel

The easiest way to deploy your Next.js app is to use the [Vercel Platform](https://vercel.com/new?utm_medium=default-template&filter=next.js&utm_source=create-next-app&utm_campaign=create-next-app-readme) from the creators of Next.js.

Check out our [Next.js deployment documentation](https://nextjs.org/docs/deployment) for more details.
