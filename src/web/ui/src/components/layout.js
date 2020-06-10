import React from 'react';
import Col from 'react-bootstrap/Col';
import Container from 'react-bootstrap/Container';
import Nav from 'react-bootstrap/Nav';
import Navbar from 'react-bootstrap/Navbar';
import NavDropdown from 'react-bootstrap/NavDropdown';
import Row from 'react-bootstrap/Row';
import { forbidExtraProps } from 'airbnb-prop-types';
import PropTypes from 'prop-types';
import Routes from '../routing/routes';
import { NAVBAR_ITEMS } from '../utils/constants';
import '../style/style.css';

function createNavigationBarContent() {
  const content = [];

  Object.entries(NAVBAR_ITEMS).forEach(([item, value]) => {
    // If the value is another object, it means we have a dropdown with a list
    // of options. Otherwise, it is a single menu item.
    if (Object.keys(value).length > 1) {
      const dropDownContent = [];
      Object.entries(value).forEach(([dropDownItem, dropDownValue]) => {
        dropDownContent.push(
          <NavDropdown.Item
            href={dropDownValue}
            className="navbar-item"
            key={`${item}-${dropDownItem}-nav-dropdown`}
          >
            {dropDownItem}
          </NavDropdown.Item>,
        );
      });
      content.push(
        <NavDropdown title={item} key={`${item}-nav-dropdown`}>
          {dropDownContent}
        </NavDropdown>,
      );
    } else {
      content.push(
        <Nav.Link href={value} key={`${item}-nav`}>{item}</Nav.Link>,
      );
    }
  });
  return content;
}

function HeaderNavigationBar({ brand }) {
  return (
    <header>
      <Navbar
        collapseOnSelect
        expand="lg"
        variant="dark"
        className="navbar-header"
      >
        <Container className="align-items-end">
          <Navbar.Brand href="/">{ brand }</Navbar.Brand>
          <Navbar.Toggle aria-controls="responsive-navbar-nav" />
          <Navbar.Collapse id="responsive-navbar-nav">
            <Nav className="ml-auto">
              {createNavigationBarContent()}
            </Nav>
          </Navbar.Collapse>
        </Container>
      </Navbar>
      <Routes />
    </header>
  );
}

function FooterBanner({ text, href }) {
  return (
    <footer className="footer-style">
      <Container className="py-3">
        <Row className="align-items-center justify-content-between">
          <Col xs="auto" className="align-self-start">
            <a
              className="link-style footer-style"
              href={href}
              target="blank"
            >
              {text}
            </a>
          </Col>
        </Row>
      </Container>
    </footer>

  );
}

HeaderNavigationBar.propTypes = forbidExtraProps({
  brand: PropTypes.string.isRequired,
});

FooterBanner.propTypes = forbidExtraProps({
  text: PropTypes.string.isRequired,
  href: PropTypes.string.isRequired,
});

export { HeaderNavigationBar, FooterBanner };
