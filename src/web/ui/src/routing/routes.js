import React from 'react';
import { Route, Switch } from 'react-router-dom';
import Dashboard from '../pages/dashboard';
import AlertLogs from '../pages/alerts/logs';
import MainSettingsPage from '../pages/settings/main';
import Preferences from '../pages/alerts/preferences';
import NodesSettingsPage from '../pages/settings/nodes';
import ReposSettingsPage from '../pages/settings/repos';
import ErrorPage from '../pages/error';
import { RESOURCE_NOT_FOUND } from '../utils/error';

function Routes() {
  return (
    <Switch>
      <Route path="/" exact render={() => (<Dashboard />)} />
      <Route path="/alerts/logs" exact render={() => (<AlertLogs />)} />
      <Route path="/settings/main" exact render={() => (<MainSettingsPage />)} />
      <Route
        path="/settings/nodes"
        exact
        render={() => (<NodesSettingsPage />)}
      />
      <Route
        path="/settings/repositories"
        exact
        render={() => (<ReposSettingsPage />)}
      />
      <Route
        path="/alerts/preferences"
        exact
        render={() => (<Preferences />)}
      />
      <Route path="*" render={() => (<ErrorPage err={RESOURCE_NOT_FOUND} />)} />
    </Switch>
  );
}

export default Routes;
