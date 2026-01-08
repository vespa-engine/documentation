export default {
  title: 'Components/Breadcrumbs',
};

export const Default = () => {
  return (
    `<ul class="breadcrumb">
      <li><span class="link">Item</span></li>
      <li><span class="link">Item</span></li>
      <li><span class="link">Item</span></li>
      <li><span class="link">Item</span></li>
    </ul>`
  );
};

Default.argTypes = {};

export const Ellipsis = () => {
  return (
    `<ul class="breadcrumb">
      <li><span class="link">Item</span></li>
      <li>
        <div class="menu">
          <a class="menu-trigger"><i class="d-icon d-more-horizontal is-small link"></i></a>
          <div class="menu-content">
            <a>Home</a>
            <a>About</a>
            <a>Contact</a>
            <a>Help</a>
          </div>
        </div>
      </li>
      <li><span class="link">Item</span></li>
    </ul>`
  );
};

Ellipsis.argTypes = {};