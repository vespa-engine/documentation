export default {
  title: 'Components/Chips',
};

// const colorMap = ['red','orange','yellow','lime','green','sky','blue','purple','violet','pink','grey','brand'];
// const variantMap = ['100','200','300','400','500','600','700','800','900'];
// has-bg-${bgColor}-${bgColorVariant} is-${textColor}-${textColorVariant}

export const Default = ({text, small, colorClass, textWeight}) => {
  return (
    `<span class="chips ${small ? 'is-small' : ''} ${colorClass} is-${textWeight}">${text}</span>`
  );
};

Default.argTypes = {
  text: { 
    defaultValue: 'Default Chip',
    control: 'text',
  },
  textWeight: {
    control: {
      type: 'select',
      options: ['light','regular','bold'],
    }
  },
  small: {
    defaultValue: false,
    control: 'boolean',
  },
  colorClass: {
    control: 'text',
  }
  // bgColor: {
  //   control: {
  //     type: 'select',
  //     options: colorMap,
  //   }
  // },
  // bgColorVariant: {
  //   control: {
  //     type: 'select',
  //     options: variantMap,
  //   }
  // },
  // textColor: {
  //   control: {
  //     type: 'select',
  //     options: colorMap,
  //   }
  // },
  // textColorVariant: {
  //   control: {
  //     type: 'select',
  //     options: variantMap,
  //   }
  // }
};

export const Modified = ({text, small, colorClass, textWeight}) => {
  return (
    `<span class="chips ${small ? 'is-small' : ''} ${colorClass} is-${textWeight}">${text}</span>`
  );
};

Modified.argTypes = {
  text: { 
    defaultValue: 'Default Chip',
    control: 'text',
  },
  textWeight: {
    defaultValue: 'bold',
    control: {
      type: 'select',
      options: ['light','regular','bold'],
    }
  },
  small: {
    defaultValue: false,
    control: 'boolean',
  },
  colorClass: {
    defaultValue: 'has-bg-violet-100 is-violet-600',
    control: 'text',
  }
};

export const Grouped = ({firstChipText, secondChipText, small}) => {
  return (
    `<span class="chip-group">
      <span class="chips ${small ? 'is-small' : ''} has-bg-purple-500">${firstChipText}</span><span class="chips ${small ? 'is-small' : ''} has-bg-purple-300">${secondChipText}</span>
    </span>`
  );
};

Grouped.argTypes = {
  firstChipText: { 
    defaultValue: 'Grouped',
    control: 'text',
  },
  secondChipText: { 
    defaultValue: 'Chip',
    control: 'text',
  },
  small: {
    defaultValue: false,
    control: 'boolean',
  }
};