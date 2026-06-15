import { Navigate, Route, Routes } from 'react-router-dom';

import { ComunicacionesPage } from '@/features/academico/pages/ComunicacionesPage';
import { ConfigurarUmbralPage } from '@/features/academico/pages/ConfigurarUmbralPage';
import { DeteccionEntregasPage } from '@/features/academico/pages/DeteccionEntregasPage';
import { ImportarCalificacionesPage } from '@/features/academico/pages/ImportarCalificacionesPage';
import { MonitoresSeguimientoPage } from '@/features/academico/pages/MonitoresSeguimientoPage';
import { NotasFinalesPage } from '@/features/academico/pages/NotasFinalesPage';
import { RankingPage } from '@/features/academico/pages/RankingPage';
import { ReportesPage } from '@/features/academico/pages/ReportesPage';
import { VistaAtrasadosPage } from '@/features/academico/pages/VistaAtrasadosPage';
import { EstructuraAcademicaPage } from '@/features/admin/pages/EstructuraAcademicaPage';
import { LogAuditoriaPage } from '@/features/admin/pages/LogAuditoriaPage';
import { PanelAuditoriaPage } from '@/features/admin/pages/PanelAuditoriaPage';
import { UsuariosPage } from '@/features/admin/pages/UsuariosPage';
import { ForgotPasswordPage } from '@/features/auth/pages/ForgotPasswordPage';
import { LoginPage } from '@/features/auth/pages/LoginPage';
import { ResetPasswordPage } from '@/features/auth/pages/ResetPasswordPage';
import { TwoFactorPage } from '@/features/auth/pages/TwoFactorPage';
import { AvisoFormPage } from '@/features/coordinacion/avisos/pages/AvisoFormPage';
import { AvisosPage } from '@/features/coordinacion/avisos/pages/AvisosPage';
import { AgendaReservasPage } from '@/features/coordinacion/coloquios/pages/AgendaReservasPage';
import { ColoquiosPage } from '@/features/coordinacion/coloquios/pages/ColoquiosPage';
import { ConvocatoriaFormPage } from '@/features/coordinacion/coloquios/pages/ConvocatoriaFormPage';
import { RegistroAcademicoPage } from '@/features/coordinacion/coloquios/pages/RegistroAcademicoPage';
import { EncuentrosPage } from '@/features/coordinacion/encuentros/pages/EncuentrosPage';
import { AsignacionesPage } from '@/features/coordinacion/equipos/pages/AsignacionesPage';
import { AsignacionMasivaPage } from '@/features/coordinacion/equipos/pages/AsignacionMasivaPage';
import { ClonarEquipoPage } from '@/features/coordinacion/equipos/pages/ClonarEquipoPage';
import { EquiposPage } from '@/features/coordinacion/equipos/pages/EquiposPage';
import { MonitoresPage } from '@/features/coordinacion/monitores/pages/MonitoresPage';
import { CoordinacionDashboardPage } from '@/features/coordinacion/pages/CoordinacionDashboardPage';
import { SetupCuatrimestrePage } from '@/features/coordinacion/setup/pages/SetupCuatrimestrePage';
import { TareaDetallePage } from '@/features/coordinacion/tareas/pages/TareaDetallePage';
import { TareaFormPage } from '@/features/coordinacion/tareas/pages/TareaFormPage';
import { TareasPage } from '@/features/coordinacion/tareas/pages/TareasPage';
import { AlumnoDashboardPage } from '@/features/alumno/pages/AlumnoDashboardPage';
import { EstadoAcademicoPage } from '@/features/alumno/pages/EstadoAcademicoPage';
import { MisAvisosPage } from '@/features/alumno/pages/MisAvisosPage';
import { MisColoquiosPage } from '@/features/alumno/pages/MisColoquiosPage';
import { DashboardPage } from '@/features/dashboard/pages/DashboardPage';
import { FacturasPage } from '@/features/finanzas/pages/FacturasPage';
import { GrillaSalarialPage } from '@/features/finanzas/pages/GrillaSalarialPage';
import { HistorialLiquidacionesPage } from '@/features/finanzas/pages/HistorialLiquidacionesPage';
import { LiquidacionesPage } from '@/features/finanzas/pages/LiquidacionesPage';
import { PerfilPage } from '@/features/perfil/pages/PerfilPage';
import { AuthLayout } from '@/layouts/AuthLayout';
import { AppLayout } from '@/shared/components/AppLayout';
import { ProtectedRoute } from '@/shared/components/ProtectedRoute';
import { RequirePermission } from '@/shared/components/RequirePermission';
import { Card } from '@/shared/components/ui/Card';

function NotFoundPage() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50 px-4">
      <Card className="max-w-md text-center">
        <div className="py-8">
          <h1 className="text-4xl font-bold text-secondary-900">404</h1>
          <p className="mt-2 text-sm text-secondary-500">Página no encontrada</p>
        </div>
      </Card>
    </div>
  );
}

export function App() {
  return (
    <Routes>
      <Route element={<AuthLayout />}>
        <Route path="/auth/login" element={<LoginPage />} />
        <Route path="/auth/2fa" element={<TwoFactorPage />} />
        <Route path="/auth/forgot" element={<ForgotPasswordPage />} />
        <Route path="/auth/reset" element={<ResetPasswordPage />} />
      </Route>

      <Route element={<ProtectedRoute />}>
        <Route element={<AppLayout />}>
          <Route path="/dashboard" element={<DashboardPage />} />

          <Route path="/coordinacion" element={
            <RequirePermission requiredPermission="coordinacion:acceso">
              <CoordinacionDashboardPage />
            </RequirePermission>
          } />
          <Route path="/coordinacion/equipos" element={
            <RequirePermission requiredPermission="equipos:asignar">
              <EquiposPage />
            </RequirePermission>
          } />
          <Route path="/coordinacion/equipos/asignaciones" element={
            <RequirePermission requiredPermission="equipos:asignar">
              <AsignacionesPage />
            </RequirePermission>
          } />
          <Route path="/coordinacion/equipos/asignacion-masiva" element={
            <RequirePermission requiredPermission="equipos:asignar">
              <AsignacionMasivaPage />
            </RequirePermission>
          } />
          <Route path="/coordinacion/equipos/clonar" element={
            <RequirePermission requiredPermission="equipos:asignar">
              <ClonarEquipoPage />
            </RequirePermission>
          } />
          <Route path="/coordinacion/avisos" element={
            <RequirePermission requiredPermission="avisos:publicar">
              <AvisosPage />
            </RequirePermission>
          } />
          <Route path="/coordinacion/avisos/nuevo" element={
            <RequirePermission requiredPermission="avisos:publicar">
              <AvisoFormPage />
            </RequirePermission>
          } />
          <Route path="/coordinacion/avisos/:id/editar" element={
            <RequirePermission requiredPermission="avisos:publicar">
              <AvisoFormPage />
            </RequirePermission>
          } />
          <Route path="/coordinacion/tareas" element={
            <RequirePermission requiredPermission="tareas:gestionar">
              <TareasPage />
            </RequirePermission>
          } />
          <Route path="/coordinacion/tareas/nueva" element={
            <RequirePermission requiredPermission="tareas:gestionar">
              <TareaFormPage />
            </RequirePermission>
          } />
          <Route path="/coordinacion/tareas/:id" element={
            <RequirePermission requiredPermission="tareas:gestionar">
              <TareaDetallePage />
            </RequirePermission>
          } />
          <Route path="/coordinacion/encuentros" element={
            <RequirePermission requiredPermission="encuentros:gestionar">
              <EncuentrosPage />
            </RequirePermission>
          } />
          <Route path="/coordinacion/coloquios" element={
            <RequirePermission requiredPermission="coloquios:gestionar">
              <ColoquiosPage />
            </RequirePermission>
          } />
          <Route path="/coordinacion/coloquios/nueva" element={
            <RequirePermission requiredPermission="coloquios:gestionar">
              <ConvocatoriaFormPage />
            </RequirePermission>
          } />
          <Route path="/coordinacion/coloquios/:id/reservas" element={
            <RequirePermission requiredPermission="coloquios:gestionar">
              <AgendaReservasPage />
            </RequirePermission>
          } />
          <Route path="/coordinacion/coloquios/registro" element={
            <RequirePermission requiredPermission="coloquios:gestionar">
              <RegistroAcademicoPage />
            </RequirePermission>
          } />
          <Route path="/coordinacion/monitores" element={
            <RequirePermission requiredPermission="monitores:ver">
              <MonitoresPage />
            </RequirePermission>
          } />
          <Route path="/coordinacion/setup" element={
            <RequirePermission requiredPermission="coordinacion:setup">
              <SetupCuatrimestrePage />
            </RequirePermission>
          } />

          {/* === ACADÉMICO (Docente) === */}
          <Route path="/academico" element={<Navigate to="/academico/importar" replace />} />
          <Route path="/academico/importar" element={
            <RequirePermission requiredPermission="calificaciones:importar">
              <ImportarCalificacionesPage />
            </RequirePermission>
          } />
          <Route path="/academico/umbral" element={
            <RequirePermission requiredPermission="calificaciones:importar">
              <ConfigurarUmbralPage />
            </RequirePermission>
          } />
          <Route path="/academico/atrasados" element={
            <RequirePermission requiredPermission="atrasados:ver">
              <VistaAtrasadosPage />
            </RequirePermission>
          } />
          <Route path="/academico/ranking" element={
            <RequirePermission requiredPermission="atrasados:ver">
              <RankingPage />
            </RequirePermission>
          } />
          <Route path="/academico/notas-finales" element={
            <RequirePermission requiredPermission="atrasados:ver">
              <NotasFinalesPage />
            </RequirePermission>
          } />
          <Route path="/academico/reportes" element={
            <RequirePermission requiredPermission="atrasados:ver">
              <ReportesPage />
            </RequirePermission>
          } />
          <Route path="/academico/entregas" element={
            <RequirePermission requiredPermission="atrasados:ver">
              <DeteccionEntregasPage />
            </RequirePermission>
          } />
          <Route path="/academico/comunicaciones" element={
            <RequirePermission requiredPermission="comunicacion:enviar">
              <ComunicacionesPage />
            </RequirePermission>
          } />
          <Route path="/academico/monitores" element={
            <RequirePermission requiredPermission="atrasados:ver">
              <MonitoresSeguimientoPage />
            </RequirePermission>
          } />

          <Route
            path="/calificaciones"
            element={<Navigate to="/academico/importar" replace />}
          />
          <Route
            path="/comunicaciones"
            element={<Navigate to="/academico/comunicaciones" replace />}
          />
          <Route
            path="/equipos"
            element={<Navigate to="/coordinacion/equipos" replace />}
          />
          <Route
            path="/encuentros"
            element={<Navigate to="/coordinacion/encuentros" replace />}
          />
          <Route
            path="/reportes"
            element={<Navigate to="/academico/reportes" replace />}
          />
          <Route
            path="/auditoria"
            element={<Navigate to="/admin/auditoria" replace />}
          />

          <Route
            path="/finanzas/liquidaciones"
            element={
              <RequirePermission requiredPermission="liquidaciones:ver">
                <LiquidacionesPage />
              </RequirePermission>
            }
          />
          <Route
            path="/finanzas/liquidaciones/historial"
            element={
              <RequirePermission requiredPermission="liquidaciones:ver">
                <HistorialLiquidacionesPage />
              </RequirePermission>
            }
          />
          <Route
            path="/finanzas/grilla-salarial"
            element={
              <RequirePermission requiredPermission="liquidaciones:configurar-salarios">
                <GrillaSalarialPage />
              </RequirePermission>
            }
          />
          <Route
            path="/finanzas/facturas"
            element={
              <RequirePermission requiredPermission="facturas:gestionar">
                <FacturasPage />
              </RequirePermission>
            }
          />
          {/* === ALUMNO === */}
          <Route path="/alumno" element={
            <RequirePermission requiredPermission="estado_academico:ver">
              <AlumnoDashboardPage />
            </RequirePermission>
          } />
          <Route path="/alumno/estado" element={
            <RequirePermission requiredPermission="estado_academico:ver">
              <EstadoAcademicoPage />
            </RequirePermission>
          } />
          <Route path="/alumno/avisos" element={
            <RequirePermission requiredPermission="aviso:confirmar">
              <MisAvisosPage />
            </RequirePermission>
          } />
          <Route path="/alumno/coloquios" element={
            <RequirePermission requiredPermission="coloquios:reservar">
              <MisColoquiosPage />
            </RequirePermission>
          } />

          <Route
            path="/admin/estructura"
            element={
              <RequirePermission requiredPermission="estructura:gestionar">
                <EstructuraAcademicaPage />
              </RequirePermission>
            }
          />
          <Route
            path="/admin/usuarios"
            element={
              <RequirePermission requiredPermission="usuarios:gestionar">
                <UsuariosPage />
              </RequirePermission>
            }
          />
          <Route
            path="/admin/auditoria"
            element={
              <RequirePermission requiredPermission="auditoria:ver">
                <PanelAuditoriaPage />
              </RequirePermission>
            }
          />
          <Route
            path="/admin/auditoria/log"
            element={
              <RequirePermission requiredPermission="auditoria:ver">
                <LogAuditoriaPage />
              </RequirePermission>
            }
          />

          <Route
            path="/perfil"
            element={
              <RequirePermission requiredPermission="perfil:editar">
                <PerfilPage />
              </RequirePermission>
            }
          />
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="*" element={<NotFoundPage />} />
        </Route>
      </Route>

      <Route path="/" element={<Navigate to="/dashboard" replace />} />
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  );
}
