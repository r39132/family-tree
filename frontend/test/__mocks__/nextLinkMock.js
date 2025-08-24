const React = require('react');
module.exports = ({ href, children, ...props }) => React.createElement('a', { href, ...props }, children);
