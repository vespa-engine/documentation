export default {
  title: 'Components/Links',
};

// Default
export const Default = ({text, small, secondary, state, subAction}) => {
  return (
    `<span class="link ${small ? 'is-small' : ''} ${secondary ? 'is-secondary' : ''} ${subAction ? 'is-sub' : ''} is-${state === "standard" ? '':state}">${text}</span>`
  );
};

Default.argTypes = {
  text: {
    defaultValue: 'Default Link',
    control: 'text',
  },
  small: {
    defaultValue: false,
    control: 'boolean',
  },
  secondary: {
    defaultValue: false,
    control: 'boolean',
  },
  state: {
    defaultValue: '',
    control: {
      type: 'select',
      options: ['standard','active','disabled'],
    }
  },
  subAction: {
    defaultValue: false,
    control: 'boolean',
  },
};

// Front Icon
export const FrontIcon = ({text, small, secondary, state, subAction, icon}) => {
  return (
    `<span class="link ${small ? 'is-small' : ''} ${secondary ? 'is-secondary' : ''} ${subAction ? 'is-sub' : ''} is-${state === "standard" ? '':state} has-icon-front"><i class="d-icon d-${icon}"></i>${text}</span>`
  );
};

FrontIcon.argTypes = {
  text: {
    defaultValue: 'Default Link',
    control: 'text',
  },
  small: {
    defaultValue: false,
    control: 'boolean',
  },
  secondary: {
    defaultValue: false,
    control: 'boolean',
  },
  state: {
    defaultValue: '',
    control: {
      type: 'select',
      options: ['standard','active','disabled'],
    }
  },
  subAction: {
    defaultValue: false,
    control: 'boolean',
  },
  icon: {
    defaultValue: 'add-circle',
    control: 'text',
  }
};

// Back Icon
export const BackIcon = ({text, small, secondary, state, subAction, icon}) => {
  return (
    `<span class="link ${small ? 'is-small' : ''} ${secondary ? 'is-secondary' : ''} ${subAction ? 'is-sub' : ''} is-${state === "standard" ? '':state} has-icon-back">${text}<i class="d-icon d-${icon}"></i></span>`
  );
};

BackIcon.argTypes = {
  text: {
    defaultValue: 'Default Link',
    control: 'text',
  },
  small: {
    defaultValue: false,
    control: 'boolean',
  },
  secondary: {
    defaultValue: false,
    control: 'boolean',
  },
  state: {
    defaultValue: '',
    control: {
      type: 'select',
      options: ['standard','active','disabled'],
    }
  },
  subAction: {
    defaultValue: false,
    control: 'boolean',
  },
  icon: {
    defaultValue: 'external',
    control: 'text',
  }
};