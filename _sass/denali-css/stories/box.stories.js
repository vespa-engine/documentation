export default {
  title: 'Components/Box',
};

export const Default = ({size}) => {
  return (
    `<div class="box" style="width: ${size}px">
      <h3>Title</h3>
      <a>Related Link</a>
    </div>`
  );
};

Default.argTypes = {
  size: {
    defaultValue: 340,
    control: 'number',
  }
};

export const Footer = ({size, footerHtml}) => {
  return (
    `<div class="box" style="width: ${size}px">
      <h3>Title</h3>
      <a>Related Link</a>
      <footer>
        ${footerHtml}
      </footer>
    </div>`
  );
};

Footer.argTypes = {
  size: {
    defaultValue: 600,
    control: 'number',
  },
  footerHtml: {
    defaultValue: '<p>This is a footer.</p>',
    control: 'text',
  }
};