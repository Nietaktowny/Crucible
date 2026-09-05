import { createContext } from 'react';
import { CrucibleClient } from '@/api/crucibleClient';

const global_client = new CrucibleClient(); 
export const ClientContext = createContext(global_client);
export const SchemaContext = createContext(await global_client.getStepsSchema());