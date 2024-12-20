const testData = {
  id: 'example',
  showHeader: true,
  currentOptionHash: '123',
  studentInfo: {
    availableDocuments: [
      { id: '1_2V-Npp1L0G3cw4lcH_ENSo_y_OV1BP3s8NdnwaFbVw', title: 'Document A' },
      { id: 'docB', title: 'Document B' },
      { id: 'docC', title: 'Document C' }
    ],
    profile: {
      email_address: 'example@example.com',
      name: {
        family_name: 'Doe',
        full_name: 'John Doe',
        given_name: 'John'
      },
      photo_url: '//lh3.googleusercontent.com/a/default-user'
    },
    documents: {
      '1_2V-Npp1L0G3cw4lcH_ENSo_y_OV1BP3s8NdnwaFbVw': {
        optionHash: '123',
        text: "This summer was AMAZING!!! First, I went to the beach with my family for two whole weeks! We stayed in this super cool beach house that had its own private pool and hot tub. My siblings and I spent hours playing in the waves and building sandcastles on the beach. We even went on a snorkeling trip and saw some really cool fish!\n\nWhen we weren't at the beach, I hung out with my friends and we had a blast! We went to the trampoline park and played laser tag. I also started reading this really good book called \"The Giver\" and it was sooo good that I couldn't put it down.\n\nMy parents took me and my siblings on a road trip to visit our grandparents in another state. It was a pretty long drive, but we made some great memories along the way. We stopped at a few theme parks and went on some really cool rides. My favorite one was this roller coaster that had loops and corkscrews!\n\nAt home, I started working on my own little garden project. I planted some flowers and herbs, and even tried to grow my own tomatoes (which didn't quite work out as planned...). It was pretty cool seeing everything grow and flourish.\n\nOverall, this summer was definitely the best one yet!",
        breakpoints: [
          {
            id: 'split0',
            tooltip: 'This is the first tooltip',
            start: 220,
            offset: 5,
            style: { textDecoration: 'underline' }
          },
          {
            id: 'split1',
            tooltip: 'This is a tooltip',
            start: 240,
            offset: 25,
            style: { textDecoration: 'underline' }
          },
          {
            id: 'split2',
            tooltip: 'This is another tooltip',
            start: 310,
            offset: 15,
            style: { backgroundColor: 'green' }
          }
        ]
      }
    }
  }
};

export default testData;
