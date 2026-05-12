USE [MSUISv7_0]
GO
/****** Object:  Table [dbo].[IncAcademicYear]    Script Date: 08-05-2026 Fri 3.39.02 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[IncAcademicYear](
	[Id] [int] NOT NULL,
	[AcademicYearCode] [nvarchar](20) NOT NULL,
	[SequenceNo] [int] NULL,
	[FromDate] [datetime] NULL,
	[ToDate] [datetime] NULL,
	[IsOpen] [bit] NULL,
	[IsActive] [bit] NULL,
	[IsDeleted] [bit] NULL,
	[CreatedBy] [bigint] NULL,
	[CreatedOn] [datetime] NULL,
	[ModifiedBy] [bigint] NULL,
	[ModifiedOn] [datetime] NULL,
	[CancellationFeeRefundEndDate] [datetime] NULL,
	[AdmissionEndDate] [datetime] NULL,
	[IsCurrentYear] [bit] NULL,
	[IsDSWApplicationStart] [bit] NULL,
	[DSWStartDate] [datetime] NULL,
	[DSWEndDate] [datetime] NULL,
	[DSWApplicationFee] [decimal](7, 2) NULL,
	[DSWYearlyBudget] [decimal](10, 2) NULL,
 CONSTRAINT [PK_IncAcademicYear] PRIMARY KEY CLUSTERED 
(
	[Id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[IncInstitutePartTermPaperMap]    Script Date: 08-05-2026 Fri 3.39.02 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[IncInstitutePartTermPaperMap](
	[Id] [bigint] NOT NULL,
	[InstituteId] [int] NOT NULL,
	[ProgInstPartTermId] [bigint] NOT NULL,
	[PartTermPaperMapId] [bigint] NOT NULL,
	[IsActive] [bit] NOT NULL,
	[IsDeleted] [bit] NOT NULL,
	[CreatedBy] [bigint] NULL,
	[CreatedOn] [datetime] NULL,
	[ModifiedBy] [bigint] NULL,
	[ModifiedOn] [datetime] NULL,
 CONSTRAINT [PK_IncInstitutePartTermPaperMap] PRIMARY KEY CLUSTERED 
(
	[Id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[IncPreferanceGroupMap]    Script Date: 08-05-2026 Fri 3.39.02 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[IncPreferanceGroupMap](
	[Id] [bigint] NOT NULL,
	[PreferenceId] [int] NOT NULL,
	[GroupId] [bigint] NOT NULL,
	[ProgrammeInstancePartTermId] [bigint] NOT NULL,
	[IsActive] [bit] NULL,
	[IsDeleted] [bit] NULL,
	[CreatedBy] [bigint] NULL,
	[CreatedOn] [datetime] NULL,
	[ModifiedBy] [bigint] NULL,
	[ModifiedOn] [datetime] NULL,
 CONSTRAINT [PK_IncPreferanceGroupMap] PRIMARY KEY CLUSTERED 
(
	[Id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[IncProgInstPartTermPaperMap]    Script Date: 08-05-2026 Fri 3.39.02 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[IncProgInstPartTermPaperMap](
	[Id] [bigint] NOT NULL,
	[ProgrammeInstancePartTermId] [bigint] NOT NULL,
	[PaperId] [bigint] NOT NULL,
	[GroupId] [bigint] NULL,
	[IsActive] [bit] NULL,
	[IsDelete] [bit] NULL,
	[CreatedBy] [bigint] NULL,
	[CreatedOn] [datetime] NULL,
	[ModifiedBy] [bigint] NULL,
	[ModifiedOn] [datetime] NULL,
 CONSTRAINT [PK_IncProgInstPartTermPaperMap] PRIMARY KEY CLUSTERED 
(
	[Id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[IncProgrammeInstance]    Script Date: 08-05-2026 Fri 3.39.02 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[IncProgrammeInstance](
	[Id] [bigint] NOT NULL,
	[ProgrammeId] [int] NOT NULL,
	[AcademicYearId] [int] NOT NULL,
	[FacultyId] [int] NOT NULL,
	[InstanceName] [nvarchar](500) NOT NULL,
	[Intake] [int] NULL,
	[AdmissionRight] [nvarchar](50) NULL,
	[IsActive] [bit] NOT NULL,
	[IsDeleted] [bit] NOT NULL,
	[CreatedBy] [bigint] NULL,
	[CreatedOn] [datetime] NULL,
	[ModifiedBy] [bigint] NULL,
	[ModifiedOn] [datetime] NULL,
 CONSTRAINT [PK_IncProgrammeInstance] PRIMARY KEY CLUSTERED 
(
	[Id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[IncProgrammeInstancePart]    Script Date: 08-05-2026 Fri 3.39.02 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[IncProgrammeInstancePart](
	[Id] [bigint] NOT NULL,
	[InstancePartName] [nvarchar](1000) NULL,
	[ProgrammeInstanceId] [bigint] NOT NULL,
	[ProgrammePartId] [int] NOT NULL,
	[MaxMarks] [int] NULL,
	[MinMarks] [int] NULL,
	[IsSeparatePassingHead] [bit] NULL,
	[IsActive] [bit] NOT NULL,
	[IsDeleted] [bit] NULL,
	[CreatedBy] [bigint] NULL,
	[CreatedOn] [datetime] NULL,
	[ModifiedBy] [bigint] NULL,
	[ModifiedOn] [datetime] NULL,
	[IsAllowPaperSelByStudent] [bit] NULL,
	[AcademicYearId] [int] NULL,
 CONSTRAINT [PK_AdmProgramInstancePart] PRIMARY KEY CLUSTERED 
(
	[Id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[IncProgrammeInstancePartTerm]    Script Date: 08-05-2026 Fri 3.39.02 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[IncProgrammeInstancePartTerm](
	[Id] [int] NOT NULL,
	[InstancePartTermName] [nvarchar](max) NULL,
	[ProgrammeBranchMapId] [int] NOT NULL,
	[SpecialisationId] [int] NOT NULL,
	[ProgrammePartId] [int] NOT NULL,
	[ProgrammeInstancePartId] [bigint] NOT NULL,
	[ProgrammePartTermId] [int] NOT NULL,
	[FacultyId] [int] NOT NULL,
	[ProgrammeId] [int] NOT NULL,
	[AcademicYearId] [int] NOT NULL,
	[ProgrammeInstanceId] [bigint] NOT NULL,
	[MinPapers] [int] NOT NULL,
	[MaxPapers] [int] NOT NULL,
	[MinMarks] [int] NULL,
	[MaxMarks] [int] NULL,
	[IsForApplication] [bit] NULL,
	[IsForAdmission] [bit] NULL,
	[Intake] [int] NULL,
	[InstanceYearId] [int] NULL,
	[IsSeparatePassingHead] [bit] NULL,
	[IsLaunch] [bit] NULL,
	[LaunchedBy] [bigint] NULL,
	[LaunchedOn] [datetime] NULL,
	[UnLaunchedBy] [bigint] NULL,
	[UnLaunchedOn] [datetime] NULL,
	[IsVerify] [bit] NULL,
	[VerifiedBy] [bigint] NULL,
	[StructureReportRemark] [nvarchar](max) NULL,
	[IsApprovedStructureReport] [bit] NULL,
	[ApprovedStructureReportBy] [bigint] NULL,
	[ApprovedStructureReportOn] [datetime] NULL,
	[AssessmentReportRemark] [nvarchar](max) NULL,
	[IsApprovedAssessmentReport] [bit] NULL,
	[ApprovedAssessmentReportBy] [bigint] NULL,
	[ApprovedAssessmentReportOn] [datetime] NULL,
	[VerifiedOn] [datetime] NULL,
	[IsAssessmentLaunched] [bit] NULL,
	[AssessmentLaunchedBy] [bigint] NULL,
	[AssessmentLaunchedOn] [datetime] NULL,
	[IsAssessmentVerified] [bit] NULL,
	[AssessmentVerifiedBy] [bigint] NULL,
	[AssessmentVerifiedOn] [datetime] NULL,
	[IsCentrallyAdmission] [bit] NULL,
	[IsCompleted] [bit] NULL,
	[CompletedBy] [bigint] NULL,
	[CompletedOn] [datetime] NULL,
	[IsCompletedAssessment] [bit] NULL,
	[AssessmentCompletedBy] [bigint] NULL,
	[AssessmentCompletedOn] [datetime] NULL,
	[IsActive] [bit] NOT NULL,
	[IsDeleted] [bit] NOT NULL,
	[CreatedBy] [bigint] NULL,
	[CreatedOn] [datetime] NULL,
	[ModifiedBy] [bigint] NULL,
	[ModifiedOn] [datetime] NULL,
	[IsPaperSelByStudent] [bit] NULL,
	[IsPaperSelBeforeFees] [bit] NULL,
	[IsPreferenceRequired] [bit] NULL,
	[IsAdmThroughGCAS] [bit] NULL,
	[IsPrerequisiteRequired] [bit] NULL,
 CONSTRAINT [PK_MstProgramInstancePartTerm] PRIMARY KEY CLUSTERED 
(
	[Id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY] TEXTIMAGE_ON [PRIMARY]
GO
/****** Object:  Table [dbo].[IncProgrammeInstancePartTermPaperGroup]    Script Date: 08-05-2026 Fri 3.39.02 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[IncProgrammeInstancePartTermPaperGroup](
	[Id] [bigint] NOT NULL,
	[ProgrammeInstancePartTermId] [bigint] NOT NULL,
	[MstPartTermGroupId] [bigint] NOT NULL,
	[ContainsSubgroup] [bit] NOT NULL,
	[IsSubGroup] [bit] NULL,
	[ParentGroupId] [bigint] NULL,
	[MinPapers] [int] NULL,
	[MaxPapers] [int] NULL,
	[MinSubgroup] [int] NULL,
	[MaxSubgroup] [int] NULL,
	[SeparatePassingHead] [bit] NULL,
	[MinMarks] [int] NULL,
	[MaxMarks] [int] NULL,
	[MinCredits] [decimal](5, 2) NULL,
	[MaxCredits] [decimal](5, 2) NULL,
	[IsActive] [bit] NULL,
	[IsDeleted] [bit] NULL,
	[CreatedBy] [bigint] NULL,
	[CreatedOn] [datetime] NULL,
	[ModifiedBy] [bigint] NULL,
	[ModifiedOn] [datetime] NULL,
 CONSTRAINT [PK_MstProgrammeInstancePaperGroup] PRIMARY KEY CLUSTERED 
(
	[Id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[IncStudentAcademicInformation]    Script Date: 08-05-2026 Fri 3.39.02 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[IncStudentAcademicInformation](
	[Id] [bigint] NOT NULL,
	[PRN] [bigint] NOT NULL,
	[StudentAdmissionId] [bigint] NOT NULL,
	[ProgrammeInstancePartId] [bigint] NULL,
	[ProgrammeInstancePartTermId] [bigint] NOT NULL,
	[ProgrammeId] [int] NOT NULL,
	[SpecialisationId] [int] NOT NULL,
	[AcademicYearId] [int] NOT NULL,
	[InstituteId] [int] NOT NULL,
	[FacultyId] [int] NOT NULL,
	[AdmissionFeeCategoryId] [int] NULL,
	[AdmissionFeeCategoryPartTermMapId] [bigint] NULL,
	[PreferenceGroupId] [int] NULL,
	[AdmissionCommitteeId] [int] NULL,
	[AllotmentNo] [nvarchar](50) NULL,
	[MeritNo] [nvarchar](50) NULL,
	[PartTermStatus] [nvarchar](50) NULL,
	[CreatedBy] [bigint] NULL,
	[CreatedOn] [datetime] NULL,
	[ModifiedBy] [bigint] NULL,
	[ModifiedOn] [datetime] NULL,
	[IsDeleted] [bit] NULL,
	[PartStatus] [nvarchar](50) NULL,
	[CancelForReAdmission] [bit] NULL,
	[IsMarkedAsTransfered] [bit] NULL,
	[IsEligibleForDegree] [bit] NULL,
	[IsLateral] [bit] NULL,
	[IsExempted] [bit] NULL,
	[DegreeExamEventId] [int] NULL,
	[IsAdmissionCancelled] [bit] NULL,
	[ExamMasterId] [int] NULL,
 CONSTRAINT [PK_IncStudentAcademicInformation] PRIMARY KEY CLUSTERED 
(
	[Id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[IncStudentAdmission]    Script Date: 08-05-2026 Fri 3.39.02 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[IncStudentAdmission](
	[Id] [bigint] NOT NULL,
	[PRN] [bigint] NOT NULL,
	[ProgrammeInstancePartId] [bigint] NOT NULL,
	[ProgrammeInstancePartTermId] [bigint] NOT NULL,
	[ProgrammeId] [int] NOT NULL,
	[SpecialisationId] [int] NOT NULL,
	[AcademicYearId] [int] NOT NULL,
	[InstituteId] [int] NOT NULL,
	[FacultyId] [int] NOT NULL,
	[AdmissionFeeCategoryId] [int] NOT NULL,
	[AdmissionFeeCategoryPartTermMapId] [bigint] NOT NULL,
	[EligibilityByFaculty] [nvarchar](500) NULL,
	[ApprovedByFaculty] [bigint] NULL,
	[ApprovedOnFaculty] [datetime] NULL,
	[AdminRemarkByFaculty] [nvarchar](3000) NULL,
	[EligibilityByAcademics] [nvarchar](100) NULL,
	[ApprovedByAcademics] [bigint] NULL,
	[ApprovedOnAcademics] [datetime] NULL,
	[AdminRemarkByAcademics] [nvarchar](3000) NULL,
	[AdmissionStatus] [nvarchar](50) NULL,
	[IsDualAdmission] [bit] NULL,
	[DualAdmissionDoc] [nvarchar](3000) NULL,
	[CreatedBy] [bigint] NULL,
	[CreatedOn] [datetime] NULL,
	[ModifiedBy] [bigint] NULL,
	[ModifiedOn] [datetime] NULL,
	[IsDeleted] [bit] NULL,
	[IsTransferAdmission] [bit] NULL,
	[TransferAdmissionRemarksByFaculty] [nvarchar](3000) NULL,
	[TransferAdmissionRemarksByAcademic] [nvarchar](3000) NULL,
	[TransferAdmissionDoc] [nvarchar](3000) NULL,
	[CancelForReAdmission] [bit] NULL,
	[IsMarkedAsTransfered] [bit] NULL,
	[IsEligibleForDegree] [bit] NULL,
	[IsLateral] [bit] NULL,
	[DegreeExamEventId] [int] NULL,
	[IsAdmissionCancelled] [bit] NULL,
	[GCAS_ApplicationNo] [nvarchar](50) NULL,
	[AdmittedGenResCategoryId] [int] NULL,
	[IsAdmittedInPHDisabled] [bit] NULL,
	[MSUIS_DisabilityId] [tinyint] NULL,
 CONSTRAINT [PK_IncStudentAdmission] PRIMARY KEY CLUSTERED 
(
	[Id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[IncStudentPartTermPaperMap]    Script Date: 08-05-2026 Fri 3.39.02 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[IncStudentPartTermPaperMap](
	[Id] [bigint] NOT NULL,
	[PRN] [bigint] NULL,
	[StudentAcademicInformationId] [bigint] NULL,
	[ProgrammeInstancePartTermId] [bigint] NULL,
	[PaperId] [bigint] NULL,
	[MstPaperId] [bigint] NULL,
	[ObtainedMarks] [decimal](4, 0) NULL,
	[ObtainedGrade] [nvarchar](4) NULL,
	[PaperStatus] [nvarchar](50) NULL,
	[PartTermStatus] [nvarchar](50) NULL,
	[IsExempted] [bit] NULL,
	[ResultStatus] [nvarchar](50) NULL,
	[CreatedBy] [bigint] NULL,
	[CreatedOn] [datetime] NULL,
	[ModifiedBy] [bigint] NULL,
	[ModifiedOn] [datetime] NULL,
	[IsDeleted] [bit] NULL,
	[IsLateral] [bit] NULL,
	[IsAdmissionCancelled] [bit] NULL,
	[Division] [nvarchar](10) NULL,
	[ExamMasterId] [int] NULL,
 CONSTRAINT [PK_IncStudentPartTermPaperMap] PRIMARY KEY CLUSTERED 
(
	[Id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[MstInstitute]    Script Date: 08-05-2026 Fri 3.39.02 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[MstInstitute](
	[Id] [int] NOT NULL,
	[InstituteName] [nvarchar](200) NOT NULL,
	[InstituteCode] [nvarchar](20) NOT NULL,
	[InstituteType] [nvarchar](20) NULL,
	[InstituteAddress] [nvarchar](max) NULL,
	[CityName] [nvarchar](50) NULL,
	[Pincode] [int] NULL,
	[InstituteContactNo] [nvarchar](15) NULL,
	[InstituteFaxNo] [nvarchar](20) NULL,
	[InstituteEmail] [nvarchar](150) NULL,
	[InstituteUrl] [nvarchar](max) NULL,
	[IsConsiderForAdmission] [bit] NOT NULL,
	[IsActive] [bit] NOT NULL,
	[IsDeleted] [bit] NOT NULL,
	[CreatedBy] [bigint] NULL,
	[CreatedOn] [datetime] NULL,
	[ModifiedBy] [bigint] NULL,
	[ModifiedOn] [datetime] NULL,
 CONSTRAINT [PK_MstInstitute] PRIMARY KEY CLUSTERED 
(
	[Id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY] TEXTIMAGE_ON [PRIMARY]
GO
/****** Object:  Table [dbo].[MstInstituteProgrammeMap]    Script Date: 08-05-2026 Fri 3.39.02 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[MstInstituteProgrammeMap](
	[Id] [int] NOT NULL,
	[InstituteId] [int] NULL,
	[ProgrammeId] [int] NULL,
	[IsActive] [bit] NOT NULL,
	[IsDeleted] [bit] NOT NULL,
	[CreatedOn] [datetime] NULL,
	[CreatedBy] [bigint] NULL,
	[ModifiedOn] [datetime] NULL,
	[ModifiedBy] [bigint] NULL,
 CONSTRAINT [PK_MstInstituteProgramMap] PRIMARY KEY CLUSTERED 
(
	[Id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[MstPaper]    Script Date: 08-05-2026 Fri 3.39.02 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[MstPaper](
	[Id] [bigint] NOT NULL,
	[SubjectId] [int] NOT NULL,
	[PaperName] [nvarchar](1000) NOT NULL,
	[PaperCode] [nvarchar](30) NOT NULL,
	[IsCredit] [bit] NOT NULL,
	[MaxMarks] [int] NULL,
	[MinMarks] [int] NULL,
	[Credits] [decimal](5, 2) NULL,
	[IsSeparatePassingHead] [bit] NOT NULL,
	[EvaluationId] [int] NULL,
	[ClassGradeTemplateId] [int] NULL,
	[IsActive] [bit] NOT NULL,
	[IsDeleted] [bit] NOT NULL,
	[CreatedBy] [bigint] NULL,
	[CreatedOn] [datetime] NULL,
	[ModifiedBy] [bigint] NULL,
	[ModifiedOn] [datetime] NULL,
 CONSTRAINT [PK_MstPaper] PRIMARY KEY CLUSTERED 
(
	[Id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[MstPaperTeachingLearningMap]    Script Date: 08-05-2026 Fri 3.39.02 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[MstPaperTeachingLearningMap](
	[Id] [bigint] NOT NULL,
	[PaperId] [bigint] NOT NULL,
	[TeachingLearningMethodId] [int] NOT NULL,
	[AssessmentMethodId] [int] NOT NULL,
	[AssessmentType] [nvarchar](15) NULL,
	[AssessmentMethodMarks] [int] NULL,
	[AssessmentTypeMinMarks] [int] NULL,
	[AssessmentTypeMaxMarks] [int] NULL,
	[IsExemption] [bit] NULL,
	[IsCarryForwarded] [bit] NULL,
	[NoOfLecturesPerWeek] [int] NULL,
	[NoOfHoursPerWeek] [decimal](5, 2) NULL,
	[NoOfCredits] [decimal](5, 2) NULL,
	[IsActive] [bit] NULL,
	[IsDeleted] [bit] NULL,
	[CreatedBy] [bigint] NULL,
	[CreatedOn] [datetime] NULL,
	[ModifiedBy] [bigint] NULL,
	[ModifiedOn] [datetime] NULL,
 CONSTRAINT [PK_MstPaperTeachingLearningMap] PRIMARY KEY CLUSTERED 
(
	[Id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[MstProgramme]    Script Date: 08-05-2026 Fri 3.39.02 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[MstProgramme](
	[Id] [int] NOT NULL,
	[ProgrammeName] [nvarchar](300) NOT NULL,
	[ProgrammeCode] [nvarchar](100) NOT NULL,
	[FacultyId] [int] NOT NULL,
	[ProgrammeDescription] [nvarchar](max) NULL,
	[ProgrammeLevelId] [int] NOT NULL,
	[ProgrammeModeId] [int] NOT NULL,
	[ProgrammeTypeId] [int] NOT NULL,
	[InstructionMediumId] [int] NOT NULL,
	[EvaluationId] [int] NOT NULL,
	[IsCBCS] [bit] NOT NULL,
	[IsSepartePassingHead] [bit] NULL,
	[MaxMarks] [int] NULL,
	[MinMarks] [int] NULL,
	[MaxCredits] [decimal](5, 2) NULL,
	[MinCredits] [decimal](5, 2) NULL,
	[ProgrammeDuration] [int] NOT NULL,
	[ProgrammeValidity] [int] NOT NULL,
	[TotalParts] [int] NOT NULL,
	[IsActive] [bit] NOT NULL,
	[IsDeleted] [bit] NOT NULL,
	[CreatedBy] [bigint] NULL,
	[CreatedOn] [datetime] NULL,
	[ModifiedBy] [bigint] NULL,
	[ModifiedOn] [datetime] NULL,
	[IsNEP] [bit] NULL,
 CONSTRAINT [PK_MstProgramme] PRIMARY KEY CLUSTERED 
(
	[Id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY] TEXTIMAGE_ON [PRIMARY]
GO
/****** Object:  Table [dbo].[MstProgrammeBranchMap]    Script Date: 08-05-2026 Fri 3.39.02 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[MstProgrammeBranchMap](
	[Id] [int] NOT NULL,
	[ProgrammeId] [int] NOT NULL,
	[SpecialisationId] [int] NOT NULL,
	[SubSpecialisationId] [int] NULL,
	[IsActive] [bit] NOT NULL,
	[IsDeleted] [bit] NOT NULL,
	[CreatedBy] [bigint] NULL,
	[CreatedOn] [datetime] NULL,
	[ModifiedBy] [bigint] NULL,
	[ModifiedOn] [datetime] NULL,
 CONSTRAINT [PK_MstProgrammeBranchMap] PRIMARY KEY CLUSTERED 
(
	[Id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[MstProgrammePart]    Script Date: 08-05-2026 Fri 3.39.02 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[MstProgrammePart](
	[Id] [int] NOT NULL,
	[ProgrammeId] [int] NOT NULL,
	[ExamPatternId] [int] NOT NULL,
	[PartName] [nvarchar](100) NULL,
	[PartShortName] [nvarchar](50) NULL,
	[SequenceNo] [bigint] NULL,
	[NoOfTerms] [bigint] NULL,
	[CreatedBy] [bigint] NULL,
	[CreatedOn] [datetime] NULL,
	[ModifiedBy] [bigint] NULL,
	[ModifiedOn] [datetime] NULL,
	[IsActive] [bit] NULL,
	[IsDeleted] [bit] NULL,
 CONSTRAINT [PK_MstProgrammePart] PRIMARY KEY CLUSTERED 
(
	[Id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY],
 CONSTRAINT [IX_MstProgrammePart] UNIQUE NONCLUSTERED 
(
	[PartName] ASC,
	[PartShortName] ASC,
	[ProgrammeId] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[MstProgrammePartTerm]    Script Date: 08-05-2026 Fri 3.39.02 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[MstProgrammePartTerm](
	[Id] [int] NOT NULL,
	[PartId] [int] NOT NULL,
	[PartTermName] [nvarchar](max) NOT NULL,
	[PartTermShortName] [nvarchar](100) NOT NULL,
	[SequenceNo] [int] NULL,
	[IsActive] [bit] NOT NULL,
	[IsDeleted] [bit] NOT NULL,
	[CreatedBy] [bigint] NULL,
	[CreatedOn] [datetime] NULL,
	[ModifiedBy] [bigint] NULL,
	[ModifiedOn] [datetime] NULL,
	[IsBranchChangeAllowed] [bit] NULL,
 CONSTRAINT [PK_MstProgrammePartTerm] PRIMARY KEY CLUSTERED 
(
	[Id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY] TEXTIMAGE_ON [PRIMARY]
GO
/****** Object:  Table [dbo].[MstProgrammePartTermPaperMap]    Script Date: 08-05-2026 Fri 3.39.02 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[MstProgrammePartTermPaperMap](
	[Id] [bigint] NOT NULL,
	[PartTermId] [int] NULL,
	[PaperId] [bigint] NULL,
	[GroupId] [bigint] NULL,
	[IsActive] [bit] NULL,
	[IsDelete] [bit] NULL,
	[CreatedBy] [bigint] NULL,
	[CreatedOn] [datetime] NULL,
	[ModifiedBy] [bigint] NULL,
	[ModifiedOn] [datetime] NULL,
 CONSTRAINT [PK_MstProgrammePartTermPaperMap] PRIMARY KEY CLUSTERED 
(
	[Id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[MstSpecialisation]    Script Date: 08-05-2026 Fri 3.39.02 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[MstSpecialisation](
	[Id] [int] NOT NULL,
	[BranchName] [nvarchar](100) NOT NULL,
	[FacultyId] [int] NOT NULL,
	[InstituteId] [int] NULL,
	[IsActive] [bit] NOT NULL,
	[IsDeleted] [bit] NOT NULL,
	[CreatedBy] [bigint] NULL,
	[CreatedOn] [datetime] NULL,
	[ModifiedBy] [bigint] NULL,
	[ModifiedOn] [datetime] NULL,
 CONSTRAINT [PK_MstSpecialisation] PRIMARY KEY CLUSTERED 
(
	[Id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[MstStudent]    Script Date: 08-05-2026 Fri 3.39.02 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[MstStudent](
	[PRN] [bigint] NOT NULL,
	[LastName] [nvarchar](50) NULL,
	[FirstName] [nvarchar](50) NULL,
	[MiddleName] [nvarchar](50) NULL,
	[NameAsPerMarksheet] [nvarchar](100) NULL,
	[Gender] [nvarchar](25) NULL,
	[ReligionId] [bigint] NULL,
	[OtherReligion] [nvarchar](20) NULL,
	[MaritalStatusId] [bigint] NULL,
	[MotherTongueId] [bigint] NULL,
	[CommunicationLanguageId] [bigint] NULL,
	[DOB] [date] NULL,
	[DOBDoc] [nvarchar](50) NULL,
	[PhotoIdDoc] [nvarchar](100) NULL,
	[BloodGroupId] [bigint] NULL,
	[HeightInCms] [decimal](18, 2) NULL,
	[WeightInKgs] [decimal](18, 2) NULL,
	[IsMajorThelesamiaStatus] [nvarchar](30) NULL,
	[IsNRI] [bit] NULL,
	[CountryIdOfCitizenship] [bigint] NULL,
	[Caste] [nvarchar](20) NULL,
	[PlaceOfBirth] [nvarchar](20) NULL,
	[PassportNumber] [nvarchar](50) NULL,
	[PassportDate] [date] NULL,
	[AadharNumber] [nvarchar](20) NULL,
	[AadharDoc] [nvarchar](50) NULL,
	[NameOnAadhar] [nvarchar](50) NULL,
	[PermanentAddress] [nvarchar](max) NULL,
	[PermanentCountryId] [bigint] NULL,
	[PermanentStateId] [bigint] NULL,
	[PermanentDistrictId] [bigint] NULL,
	[PermanentCityVillage] [nvarchar](50) NULL,
	[PermanentPincode] [bigint] NULL,
	[IsCurrentAsPermanent] [bit] NULL,
	[CurrentAddress] [nvarchar](max) NULL,
	[CurrentCountryId] [bigint] NULL,
	[CurrentStateId] [bigint] NULL,
	[CurrentDistrictId] [bigint] NULL,
	[CurrentCityVillage] [nvarchar](50) NULL,
	[CurrentPincode] [bigint] NULL,
	[NameOfFather] [nvarchar](50) NULL,
	[NameOfMother] [nvarchar](50) NULL,
	[FatherMotherContactNo] [nvarchar](20) NULL,
	[SpouseName] [nvarchar](50) NULL,
	[SocialCategoryId] [bigint] NULL,
	[GSocialCategoryId] [bigint] NULL,
	[IsSocialDocSubmitted] [bit] NULL,
	[IsEWSDocSubmitted] [bit] NULL,
	[IsPCDocSubmitted] [bit] NULL,
	[IsReservationDocSubmitted] [bit] NULL,
	[SocialCategoryDoc] [nvarchar](50) NULL,
	[ReservationCategoryDoc] [nvarchar](max) NULL,
	[ApplicationCategoryId] [bigint] NULL,
	[GuardianName] [nvarchar](50) NULL,
	[GuardianContactNo] [nvarchar](50) NULL,
	[FamilyAnnualIncome] [bigint] NULL,
	[OccupationIdOfFather] [bigint] NULL,
	[OccupationIdOfMother] [bigint] NULL,
	[OccupationIdOfGuardian] [bigint] NULL,
	[IsEmp] [bit] NULL,
	[CurrentEmployerName] [nvarchar](50) NULL,
	[IsGuardianEbc] [bit] NULL,
	[GuardianAnnualIncome] [bigint] NULL,
	[EmailId] [nvarchar](50) NULL,
	[MobileNo] [nvarchar](50) NULL,
	[OptionalMobileNo] [nvarchar](50) NULL,
	[IsSmsPermissionGiven] [bit] NULL,
	[IsLocalToVadodara] [bit] NULL,
	[ActivityId] [bigint] NULL,
	[ActivityName] [nvarchar](50) NULL,
	[ParticipationLevelsId] [bigint] NULL,
	[SecuredRankId] [bigint] NULL,
	[IsEWS] [nvarchar](50) NULL,
	[EWSDoc] [nvarchar](max) NULL,
	[IsPhysicallyChallenged] [nvarchar](50) NULL,
	[PCDoc] [nvarchar](max) NULL,
	[DisabilityPercentage] [bigint] NULL,
	[DisabilityType] [nvarchar](50) NULL,
	[StudentPhoto] [nvarchar](max) NULL,
	[StudentSignature] [nvarchar](max) NULL,
	[IsTransferFromApplicant] [bit] NULL,
	[IsEmailSend] [bit] NULL,
	[EmailSendOn] [datetime] NULL,
	[IsSMSSend] [bit] NULL,
	[SMSSendOn] [datetime] NULL,
	[CreatedBy] [bigint] NULL,
	[CreatedOn] [datetime] NULL,
	[ModifiedBy] [bigint] NULL,
	[ModifiedOn] [datetime] NULL,
	[ABCId] [bigint] NULL,
	[IsLastQualifyMS] [bit] NULL,
	[FacultyId] [int] NULL,
	[ProgrammeName] [nvarchar](100) NULL,
	[PRNorEnrollNo] [nvarchar](30) NULL,
	[PassingYear] [int] NULL,
	[AdmissionYear] [int] NULL,
	[NCLCerti] [nvarchar](max) NULL,
	[NCLCertiNo] [nvarchar](30) NULL,
	[NCLCerti_IsuueDate] [date] NULL,
	[NCLCertiValidityDate] [date] NULL,
	[EWS_IADoc] [nvarchar](50) NULL,
	[EWSCertiNo] [nvarchar](30) NULL,
	[EWSCerti_IsuueDate] [date] NULL,
	[EWSCertiValidityDate] [date] NULL,
	[GCAS_ApplicationNo] [nvarchar](50) NULL,
	[GCAS_ApplicantName] [nvarchar](100) NULL,
	[NameAsPerABCId] [nchar](100) NULL,
	[DeviceToken] [nvarchar](255) NULL,
 CONSTRAINT [PK_MstStudent] PRIMARY KEY CLUSTERED 
(
	[PRN] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY] TEXTIMAGE_ON [PRIMARY]
GO
/****** Object:  Table [dbo].[MstSubSpecialisation]    Script Date: 08-05-2026 Fri 3.39.02 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[MstSubSpecialisation](
	[Id] [int] IDENTITY(1,1) NOT NULL,
	[SpecialisationId] [int] NOT NULL,
	[SubSpecialisationName] [nvarchar](50) NOT NULL,
	[IsActive] [bit] NOT NULL,
	[IsDeleted] [bit] NOT NULL,
	[CreatedBy] [bigint] NULL,
	[CreatedOn] [datetime] NULL,
	[ModifiedBy] [bigint] NULL,
	[ModifiedOn] [datetime] NULL,
 CONSTRAINT [PK_MstSubSpecialisation] PRIMARY KEY CLUSTERED 
(
	[Id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO
ALTER TABLE [dbo].[IncProgrammeInstancePart] ADD  CONSTRAINT [DF_IncProgrammeInstancePart_IsSeparatePassingHead]  DEFAULT ((0)) FOR [IsSeparatePassingHead]
GO
ALTER TABLE [dbo].[IncProgrammeInstancePartTerm] ADD  CONSTRAINT [DF_IncProgrammeInstancePartTerm_IsSeparatePassingHead]  DEFAULT ((0)) FOR [IsSeparatePassingHead]
GO
ALTER TABLE [dbo].[IncProgrammeInstancePartTermPaperGroup] ADD  CONSTRAINT [DF_IncProgrammeInstancePartTermPaperGroup_SeparatePassingHead]  DEFAULT ((0)) FOR [SeparatePassingHead]
GO
ALTER TABLE [dbo].[MstInstitute] ADD  CONSTRAINT [DF_MstInstitute_IsConsiderForAdmission]  DEFAULT ((1)) FOR [IsConsiderForAdmission]
GO
ALTER TABLE [dbo].[MstPaperTeachingLearningMap] ADD  CONSTRAINT [DF_MstPaperTeachingLearningMap_AssessmentTypeMinMarks]  DEFAULT ((0)) FOR [AssessmentTypeMinMarks]
GO
ALTER TABLE [dbo].[MstPaperTeachingLearningMap] ADD  CONSTRAINT [DF_MstPaperTeachingLearningMap_AssessmentTypeMaxMarks]  DEFAULT ((0)) FOR [AssessmentTypeMaxMarks]
GO
ALTER TABLE [dbo].[MstStudent] ADD  CONSTRAINT [DF_MstStudent_IsTransferFromApplicant]  DEFAULT ((0)) FOR [IsTransferFromApplicant]
GO
ALTER TABLE [dbo].[IncInstitutePartTermPaperMap]  WITH CHECK ADD  CONSTRAINT [FK_IncInstitutePartTermPaperMap_IncProgInstPartTermPaperMap] FOREIGN KEY([PartTermPaperMapId])
REFERENCES [dbo].[IncProgInstPartTermPaperMap] ([Id])
GO
ALTER TABLE [dbo].[IncInstitutePartTermPaperMap] CHECK CONSTRAINT [FK_IncInstitutePartTermPaperMap_IncProgInstPartTermPaperMap]
GO
ALTER TABLE [dbo].[IncInstitutePartTermPaperMap]  WITH CHECK ADD  CONSTRAINT [FK_IncInstitutePartTermPaperMap_MstInstitute] FOREIGN KEY([InstituteId])
REFERENCES [dbo].[MstInstitute] ([Id])
GO
ALTER TABLE [dbo].[IncInstitutePartTermPaperMap] CHECK CONSTRAINT [FK_IncInstitutePartTermPaperMap_MstInstitute]
GO
ALTER TABLE [dbo].[IncPreferanceGroupMap]  WITH CHECK ADD  CONSTRAINT [FK_IncPreferanceGroupMap_IncProgrammeInstancePartTermPaperGroup] FOREIGN KEY([GroupId])
REFERENCES [dbo].[IncProgrammeInstancePartTermPaperGroup] ([Id])
GO
ALTER TABLE [dbo].[IncPreferanceGroupMap] CHECK CONSTRAINT [FK_IncPreferanceGroupMap_IncProgrammeInstancePartTermPaperGroup]
GO
ALTER TABLE [dbo].[IncPreferanceGroupMap]  WITH CHECK ADD  CONSTRAINT [FK_IncPreferanceGroupMap_MstPreferenceGroup] FOREIGN KEY([PreferenceId])
REFERENCES [dbo].[MstPreferenceGroup] ([Id])
GO
ALTER TABLE [dbo].[IncPreferanceGroupMap] CHECK CONSTRAINT [FK_IncPreferanceGroupMap_MstPreferenceGroup]
GO
ALTER TABLE [dbo].[IncProgInstPartTermPaperMap]  WITH CHECK ADD  CONSTRAINT [FK_IncProgInstPartTermPaperMap_IncProgrammeInstancePartTermPaperGroup] FOREIGN KEY([GroupId])
REFERENCES [dbo].[IncProgrammeInstancePartTermPaperGroup] ([Id])
GO
ALTER TABLE [dbo].[IncProgInstPartTermPaperMap] CHECK CONSTRAINT [FK_IncProgInstPartTermPaperMap_IncProgrammeInstancePartTermPaperGroup]
GO
ALTER TABLE [dbo].[IncProgInstPartTermPaperMap]  WITH CHECK ADD  CONSTRAINT [FK_IncProgInstPartTermPaperMap_MstPaper] FOREIGN KEY([PaperId])
REFERENCES [dbo].[MstPaper] ([Id])
GO
ALTER TABLE [dbo].[IncProgInstPartTermPaperMap] CHECK CONSTRAINT [FK_IncProgInstPartTermPaperMap_MstPaper]
GO
ALTER TABLE [dbo].[IncProgrammeInstance]  WITH CHECK ADD  CONSTRAINT [FK_IncProgrammeInstance_IncAcademicYear] FOREIGN KEY([AcademicYearId])
REFERENCES [dbo].[IncAcademicYear] ([Id])
GO
ALTER TABLE [dbo].[IncProgrammeInstance] CHECK CONSTRAINT [FK_IncProgrammeInstance_IncAcademicYear]
GO
ALTER TABLE [dbo].[IncProgrammeInstance]  WITH CHECK ADD  CONSTRAINT [FK_IncProgrammeInstance_MstFaculty] FOREIGN KEY([FacultyId])
REFERENCES [dbo].[MstFaculty] ([Id])
GO
ALTER TABLE [dbo].[IncProgrammeInstance] CHECK CONSTRAINT [FK_IncProgrammeInstance_MstFaculty]
GO
ALTER TABLE [dbo].[IncProgrammeInstance]  WITH CHECK ADD  CONSTRAINT [FK_IncProgrammeInstance_MstProgramme] FOREIGN KEY([ProgrammeId])
REFERENCES [dbo].[MstProgramme] ([Id])
GO
ALTER TABLE [dbo].[IncProgrammeInstance] CHECK CONSTRAINT [FK_IncProgrammeInstance_MstProgramme]
GO
ALTER TABLE [dbo].[IncProgrammeInstancePart]  WITH CHECK ADD  CONSTRAINT [FK_AdmProgramInstancePart_MstProgrammePart] FOREIGN KEY([ProgrammePartId])
REFERENCES [dbo].[MstProgrammePart] ([Id])
GO
ALTER TABLE [dbo].[IncProgrammeInstancePart] CHECK CONSTRAINT [FK_AdmProgramInstancePart_MstProgrammePart]
GO
ALTER TABLE [dbo].[IncProgrammeInstancePart]  WITH NOCHECK ADD  CONSTRAINT [FK_IncProgrammeInstancePart_IncProgrammeInstance] FOREIGN KEY([ProgrammeInstanceId])
REFERENCES [dbo].[IncProgrammeInstance] ([Id])
GO
ALTER TABLE [dbo].[IncProgrammeInstancePart] CHECK CONSTRAINT [FK_IncProgrammeInstancePart_IncProgrammeInstance]
GO
ALTER TABLE [dbo].[IncProgrammeInstancePartTerm]  WITH CHECK ADD  CONSTRAINT [FK_IncProgramInstancePartTerm_MstProgrammePart] FOREIGN KEY([ProgrammePartId])
REFERENCES [dbo].[MstProgrammePart] ([Id])
GO
ALTER TABLE [dbo].[IncProgrammeInstancePartTerm] CHECK CONSTRAINT [FK_IncProgramInstancePartTerm_MstProgrammePart]
GO
ALTER TABLE [dbo].[IncProgrammeInstancePartTerm]  WITH CHECK ADD  CONSTRAINT [FK_IncProgramInstancePartTerm_MstProgrammePartTerm] FOREIGN KEY([ProgrammePartTermId])
REFERENCES [dbo].[MstProgrammePartTerm] ([Id])
GO
ALTER TABLE [dbo].[IncProgrammeInstancePartTerm] CHECK CONSTRAINT [FK_IncProgramInstancePartTerm_MstProgrammePartTerm]
GO
ALTER TABLE [dbo].[IncProgrammeInstancePartTerm]  WITH CHECK ADD  CONSTRAINT [FK_IncProgramInstancePartTerm_MstSpecialisation] FOREIGN KEY([SpecialisationId])
REFERENCES [dbo].[MstSpecialisation] ([Id])
GO
ALTER TABLE [dbo].[IncProgrammeInstancePartTerm] CHECK CONSTRAINT [FK_IncProgramInstancePartTerm_MstSpecialisation]
GO
ALTER TABLE [dbo].[IncProgrammeInstancePartTerm]  WITH CHECK ADD  CONSTRAINT [FK_IncProgrammeInstancePartTerm_IncAcademicYear] FOREIGN KEY([AcademicYearId])
REFERENCES [dbo].[IncAcademicYear] ([Id])
GO
ALTER TABLE [dbo].[IncProgrammeInstancePartTerm] CHECK CONSTRAINT [FK_IncProgrammeInstancePartTerm_IncAcademicYear]
GO
ALTER TABLE [dbo].[IncProgrammeInstancePartTerm]  WITH CHECK ADD  CONSTRAINT [FK_IncProgrammeInstancePartTerm_IncProgrammeInstance] FOREIGN KEY([ProgrammeInstanceId])
REFERENCES [dbo].[IncProgrammeInstance] ([Id])
GO
ALTER TABLE [dbo].[IncProgrammeInstancePartTerm] CHECK CONSTRAINT [FK_IncProgrammeInstancePartTerm_IncProgrammeInstance]
GO
ALTER TABLE [dbo].[IncProgrammeInstancePartTerm]  WITH CHECK ADD  CONSTRAINT [FK_IncProgrammeInstancePartTerm_IncProgrammeInstancePart] FOREIGN KEY([ProgrammeInstancePartId])
REFERENCES [dbo].[IncProgrammeInstancePart] ([Id])
GO
ALTER TABLE [dbo].[IncProgrammeInstancePartTerm] CHECK CONSTRAINT [FK_IncProgrammeInstancePartTerm_IncProgrammeInstancePart]
GO
ALTER TABLE [dbo].[IncProgrammeInstancePartTerm]  WITH CHECK ADD  CONSTRAINT [FK_IncProgrammeInstancePartTerm_MstFaculty] FOREIGN KEY([FacultyId])
REFERENCES [dbo].[MstFaculty] ([Id])
GO
ALTER TABLE [dbo].[IncProgrammeInstancePartTerm] CHECK CONSTRAINT [FK_IncProgrammeInstancePartTerm_MstFaculty]
GO
ALTER TABLE [dbo].[IncProgrammeInstancePartTerm]  WITH CHECK ADD  CONSTRAINT [FK_IncProgrammeInstancePartTerm_MstProgrammePartTerm] FOREIGN KEY([ProgrammePartTermId])
REFERENCES [dbo].[MstProgrammePartTerm] ([Id])
GO
ALTER TABLE [dbo].[IncProgrammeInstancePartTerm] CHECK CONSTRAINT [FK_IncProgrammeInstancePartTerm_MstProgrammePartTerm]
GO
ALTER TABLE [dbo].[IncProgrammeInstancePartTerm]  WITH CHECK ADD  CONSTRAINT [FK_MstProgramInstancePartTerm_IncProgramInstancePart] FOREIGN KEY([ProgrammeInstancePartId])
REFERENCES [dbo].[IncProgrammeInstancePart] ([Id])
GO
ALTER TABLE [dbo].[IncProgrammeInstancePartTerm] CHECK CONSTRAINT [FK_MstProgramInstancePartTerm_IncProgramInstancePart]
GO
ALTER TABLE [dbo].[IncProgrammeInstancePartTerm]  WITH CHECK ADD  CONSTRAINT [FK_MstProgramInstancePartTerm_IncProgrammeInstance] FOREIGN KEY([ProgrammeInstanceId])
REFERENCES [dbo].[IncProgrammeInstance] ([Id])
GO
ALTER TABLE [dbo].[IncProgrammeInstancePartTerm] CHECK CONSTRAINT [FK_MstProgramInstancePartTerm_IncProgrammeInstance]
GO
ALTER TABLE [dbo].[IncProgrammeInstancePartTerm]  WITH CHECK ADD  CONSTRAINT [FK_MstProgramInstancePartTerm_MstFaculty] FOREIGN KEY([FacultyId])
REFERENCES [dbo].[MstFaculty] ([Id])
GO
ALTER TABLE [dbo].[IncProgrammeInstancePartTerm] CHECK CONSTRAINT [FK_MstProgramInstancePartTerm_MstFaculty]
GO
ALTER TABLE [dbo].[IncProgrammeInstancePartTerm]  WITH CHECK ADD  CONSTRAINT [FK_MstProgramInstancePartTerm_MstProgramme] FOREIGN KEY([ProgrammeId])
REFERENCES [dbo].[MstProgramme] ([Id])
GO
ALTER TABLE [dbo].[IncProgrammeInstancePartTerm] CHECK CONSTRAINT [FK_MstProgramInstancePartTerm_MstProgramme]
GO
ALTER TABLE [dbo].[IncProgrammeInstancePartTerm]  WITH CHECK ADD  CONSTRAINT [FK_MstProgramInstancePartTerm_MstProgrammeBranchMap] FOREIGN KEY([ProgrammeBranchMapId])
REFERENCES [dbo].[MstProgrammeBranchMap] ([Id])
GO
ALTER TABLE [dbo].[IncProgrammeInstancePartTerm] CHECK CONSTRAINT [FK_MstProgramInstancePartTerm_MstProgrammeBranchMap]
GO
ALTER TABLE [dbo].[IncProgrammeInstancePartTermPaperGroup]  WITH CHECK ADD  CONSTRAINT [FK_IncProgrammeInstancePartTermPaperGroup_IncProgrammeInstancePartTermPaperGroup] FOREIGN KEY([MstPartTermGroupId])
REFERENCES [dbo].[MstPartTermGroupMap] ([Id])
GO
ALTER TABLE [dbo].[IncProgrammeInstancePartTermPaperGroup] CHECK CONSTRAINT [FK_IncProgrammeInstancePartTermPaperGroup_IncProgrammeInstancePartTermPaperGroup]
GO
ALTER TABLE [dbo].[IncProgrammeInstancePartTermPaperGroup]  WITH CHECK ADD  CONSTRAINT [FK_MstProgrammeInstancePaperGroup_MstProgrammeInstancePaperGroup] FOREIGN KEY([ParentGroupId])
REFERENCES [dbo].[IncProgrammeInstancePartTermPaperGroup] ([Id])
GO
ALTER TABLE [dbo].[IncProgrammeInstancePartTermPaperGroup] CHECK CONSTRAINT [FK_MstProgrammeInstancePaperGroup_MstProgrammeInstancePaperGroup]
GO
ALTER TABLE [dbo].[IncStudentAcademicInformation]  WITH CHECK ADD  CONSTRAINT [FK_IncStudentAcademicInformation_ExamEventMaster] FOREIGN KEY([DegreeExamEventId])
REFERENCES [dbo].[ExamEventMaster] ([Id])
GO
ALTER TABLE [dbo].[IncStudentAcademicInformation] CHECK CONSTRAINT [FK_IncStudentAcademicInformation_ExamEventMaster]
GO
ALTER TABLE [dbo].[IncStudentAcademicInformation]  WITH CHECK ADD  CONSTRAINT [FK_IncStudentAcademicInformation_FeeCategoryPartTermMap] FOREIGN KEY([AdmissionFeeCategoryPartTermMapId])
REFERENCES [dbo].[FeeCategoryPartTermMap] ([Id])
GO
ALTER TABLE [dbo].[IncStudentAcademicInformation] CHECK CONSTRAINT [FK_IncStudentAcademicInformation_FeeCategoryPartTermMap]
GO
ALTER TABLE [dbo].[IncStudentAcademicInformation]  WITH CHECK ADD  CONSTRAINT [FK_IncStudentAcademicInformation_IncAcademicYear] FOREIGN KEY([AcademicYearId])
REFERENCES [dbo].[IncAcademicYear] ([Id])
GO
ALTER TABLE [dbo].[IncStudentAcademicInformation] CHECK CONSTRAINT [FK_IncStudentAcademicInformation_IncAcademicYear]
GO
ALTER TABLE [dbo].[IncStudentAcademicInformation]  WITH CHECK ADD  CONSTRAINT [FK_IncStudentAcademicInformation_IncProgrammeInstancePart] FOREIGN KEY([ProgrammeInstancePartId])
REFERENCES [dbo].[IncProgrammeInstancePart] ([Id])
GO
ALTER TABLE [dbo].[IncStudentAcademicInformation] CHECK CONSTRAINT [FK_IncStudentAcademicInformation_IncProgrammeInstancePart]
GO
ALTER TABLE [dbo].[IncStudentAcademicInformation]  WITH CHECK ADD  CONSTRAINT [FK_IncStudentAcademicInformation_IncStudentAdmission] FOREIGN KEY([StudentAdmissionId])
REFERENCES [dbo].[IncStudentAdmission] ([Id])
GO
ALTER TABLE [dbo].[IncStudentAcademicInformation] CHECK CONSTRAINT [FK_IncStudentAcademicInformation_IncStudentAdmission]
GO
ALTER TABLE [dbo].[IncStudentAcademicInformation]  WITH CHECK ADD  CONSTRAINT [FK_IncStudentAcademicInformation_MstAdmissionCommittee] FOREIGN KEY([AdmissionCommitteeId])
REFERENCES [dbo].[MstAdmissionCommittee] ([Id])
GO
ALTER TABLE [dbo].[IncStudentAcademicInformation] CHECK CONSTRAINT [FK_IncStudentAcademicInformation_MstAdmissionCommittee]
GO
ALTER TABLE [dbo].[IncStudentAcademicInformation]  WITH CHECK ADD  CONSTRAINT [FK_IncStudentAcademicInformation_MstFaculty] FOREIGN KEY([FacultyId])
REFERENCES [dbo].[MstFaculty] ([Id])
GO
ALTER TABLE [dbo].[IncStudentAcademicInformation] CHECK CONSTRAINT [FK_IncStudentAcademicInformation_MstFaculty]
GO
ALTER TABLE [dbo].[IncStudentAcademicInformation]  WITH CHECK ADD  CONSTRAINT [FK_IncStudentAcademicInformation_MstFeeCategory] FOREIGN KEY([AdmissionFeeCategoryId])
REFERENCES [dbo].[MstFeeCategory] ([Id])
GO
ALTER TABLE [dbo].[IncStudentAcademicInformation] CHECK CONSTRAINT [FK_IncStudentAcademicInformation_MstFeeCategory]
GO
ALTER TABLE [dbo].[IncStudentAcademicInformation]  WITH CHECK ADD  CONSTRAINT [FK_IncStudentAcademicInformation_MstInstitute] FOREIGN KEY([InstituteId])
REFERENCES [dbo].[MstInstitute] ([Id])
GO
ALTER TABLE [dbo].[IncStudentAcademicInformation] CHECK CONSTRAINT [FK_IncStudentAcademicInformation_MstInstitute]
GO
ALTER TABLE [dbo].[IncStudentAcademicInformation]  WITH CHECK ADD  CONSTRAINT [FK_IncStudentAcademicInformation_MstPreferenceGroup] FOREIGN KEY([PreferenceGroupId])
REFERENCES [dbo].[MstPreferenceGroup] ([Id])
GO
ALTER TABLE [dbo].[IncStudentAcademicInformation] CHECK CONSTRAINT [FK_IncStudentAcademicInformation_MstPreferenceGroup]
GO
ALTER TABLE [dbo].[IncStudentAcademicInformation]  WITH CHECK ADD  CONSTRAINT [FK_IncStudentAcademicInformation_MstProgramme] FOREIGN KEY([ProgrammeId])
REFERENCES [dbo].[MstProgramme] ([Id])
GO
ALTER TABLE [dbo].[IncStudentAcademicInformation] CHECK CONSTRAINT [FK_IncStudentAcademicInformation_MstProgramme]
GO
ALTER TABLE [dbo].[IncStudentAcademicInformation]  WITH CHECK ADD  CONSTRAINT [FK_IncStudentAcademicInformation_MstSpecialisation] FOREIGN KEY([SpecialisationId])
REFERENCES [dbo].[MstSpecialisation] ([Id])
GO
ALTER TABLE [dbo].[IncStudentAcademicInformation] CHECK CONSTRAINT [FK_IncStudentAcademicInformation_MstSpecialisation]
GO
ALTER TABLE [dbo].[IncStudentAcademicInformation]  WITH CHECK ADD  CONSTRAINT [FK_IncStudentAcademicInformation_MstStudent] FOREIGN KEY([PRN])
REFERENCES [dbo].[MstStudent] ([PRN])
GO
ALTER TABLE [dbo].[IncStudentAcademicInformation] CHECK CONSTRAINT [FK_IncStudentAcademicInformation_MstStudent]
GO
ALTER TABLE [dbo].[IncStudentAdmission]  WITH CHECK ADD  CONSTRAINT [FK_IncStudentAdmission_ExamEventMaster] FOREIGN KEY([DegreeExamEventId])
REFERENCES [dbo].[ExamEventMaster] ([Id])
GO
ALTER TABLE [dbo].[IncStudentAdmission] CHECK CONSTRAINT [FK_IncStudentAdmission_ExamEventMaster]
GO
ALTER TABLE [dbo].[IncStudentAdmission]  WITH CHECK ADD  CONSTRAINT [FK_IncStudentAdmission_FeeCategoryPartTermMap] FOREIGN KEY([AdmissionFeeCategoryPartTermMapId])
REFERENCES [dbo].[FeeCategoryPartTermMap] ([Id])
GO
ALTER TABLE [dbo].[IncStudentAdmission] CHECK CONSTRAINT [FK_IncStudentAdmission_FeeCategoryPartTermMap]
GO
ALTER TABLE [dbo].[IncStudentAdmission]  WITH CHECK ADD  CONSTRAINT [FK_IncStudentAdmission_IncAcademicYear] FOREIGN KEY([AcademicYearId])
REFERENCES [dbo].[IncAcademicYear] ([Id])
GO
ALTER TABLE [dbo].[IncStudentAdmission] CHECK CONSTRAINT [FK_IncStudentAdmission_IncAcademicYear]
GO
ALTER TABLE [dbo].[IncStudentAdmission]  WITH CHECK ADD  CONSTRAINT [FK_IncStudentAdmission_IncProgrammeInstancePart] FOREIGN KEY([ProgrammeInstancePartId])
REFERENCES [dbo].[IncProgrammeInstancePart] ([Id])
GO
ALTER TABLE [dbo].[IncStudentAdmission] CHECK CONSTRAINT [FK_IncStudentAdmission_IncProgrammeInstancePart]
GO
ALTER TABLE [dbo].[IncStudentAdmission]  WITH CHECK ADD  CONSTRAINT [FK_IncStudentAdmission_IncProgrammeInstancePartTerm] FOREIGN KEY([SpecialisationId])
REFERENCES [dbo].[MstSpecialisation] ([Id])
GO
ALTER TABLE [dbo].[IncStudentAdmission] CHECK CONSTRAINT [FK_IncStudentAdmission_IncProgrammeInstancePartTerm]
GO
ALTER TABLE [dbo].[IncStudentAdmission]  WITH CHECK ADD  CONSTRAINT [FK_IncStudentAdmission_MstFaculty] FOREIGN KEY([FacultyId])
REFERENCES [dbo].[MstFaculty] ([Id])
GO
ALTER TABLE [dbo].[IncStudentAdmission] CHECK CONSTRAINT [FK_IncStudentAdmission_MstFaculty]
GO
ALTER TABLE [dbo].[IncStudentAdmission]  WITH CHECK ADD  CONSTRAINT [FK_IncStudentAdmission_MstFeeCategory] FOREIGN KEY([AdmissionFeeCategoryId])
REFERENCES [dbo].[MstFeeCategory] ([Id])
GO
ALTER TABLE [dbo].[IncStudentAdmission] CHECK CONSTRAINT [FK_IncStudentAdmission_MstFeeCategory]
GO
ALTER TABLE [dbo].[IncStudentAdmission]  WITH CHECK ADD  CONSTRAINT [FK_IncStudentAdmission_MstInstitute] FOREIGN KEY([InstituteId])
REFERENCES [dbo].[MstInstitute] ([Id])
GO
ALTER TABLE [dbo].[IncStudentAdmission] CHECK CONSTRAINT [FK_IncStudentAdmission_MstInstitute]
GO
ALTER TABLE [dbo].[IncStudentAdmission]  WITH CHECK ADD  CONSTRAINT [FK_IncStudentAdmission_MstProgramme] FOREIGN KEY([ProgrammeId])
REFERENCES [dbo].[MstProgramme] ([Id])
GO
ALTER TABLE [dbo].[IncStudentAdmission] CHECK CONSTRAINT [FK_IncStudentAdmission_MstProgramme]
GO
ALTER TABLE [dbo].[IncStudentAdmission]  WITH CHECK ADD  CONSTRAINT [FK_IncStudentAdmission_MstStudent] FOREIGN KEY([PRN])
REFERENCES [dbo].[MstStudent] ([PRN])
GO
ALTER TABLE [dbo].[IncStudentAdmission] CHECK CONSTRAINT [FK_IncStudentAdmission_MstStudent]
GO
ALTER TABLE [dbo].[IncStudentPartTermPaperMap]  WITH CHECK ADD  CONSTRAINT [FK_IncStudentPartTermPaperMap_IncProgInstPartTermPaperMap] FOREIGN KEY([PaperId])
REFERENCES [dbo].[IncProgInstPartTermPaperMap] ([Id])
GO
ALTER TABLE [dbo].[IncStudentPartTermPaperMap] CHECK CONSTRAINT [FK_IncStudentPartTermPaperMap_IncProgInstPartTermPaperMap]
GO
ALTER TABLE [dbo].[IncStudentPartTermPaperMap]  WITH CHECK ADD  CONSTRAINT [FK_IncStudentPartTermPaperMap_IncStudentAcademicInformation] FOREIGN KEY([StudentAcademicInformationId])
REFERENCES [dbo].[IncStudentAcademicInformation] ([Id])
GO
ALTER TABLE [dbo].[IncStudentPartTermPaperMap] CHECK CONSTRAINT [FK_IncStudentPartTermPaperMap_IncStudentAcademicInformation]
GO
ALTER TABLE [dbo].[IncStudentPartTermPaperMap]  WITH CHECK ADD  CONSTRAINT [FK_IncStudentPartTermPaperMap_MstPaper] FOREIGN KEY([MstPaperId])
REFERENCES [dbo].[MstPaper] ([Id])
GO
ALTER TABLE [dbo].[IncStudentPartTermPaperMap] CHECK CONSTRAINT [FK_IncStudentPartTermPaperMap_MstPaper]
GO
ALTER TABLE [dbo].[IncStudentPartTermPaperMap]  WITH CHECK ADD  CONSTRAINT [FK_IncStudentPartTermPaperMap_MstStudent] FOREIGN KEY([PRN])
REFERENCES [dbo].[MstStudent] ([PRN])
GO
ALTER TABLE [dbo].[IncStudentPartTermPaperMap] CHECK CONSTRAINT [FK_IncStudentPartTermPaperMap_MstStudent]
GO
ALTER TABLE [dbo].[MstInstituteProgrammeMap]  WITH CHECK ADD  CONSTRAINT [FK_MstInstituteProgrammeMap_MstInstitute] FOREIGN KEY([InstituteId])
REFERENCES [dbo].[MstInstitute] ([Id])
GO
ALTER TABLE [dbo].[MstInstituteProgrammeMap] CHECK CONSTRAINT [FK_MstInstituteProgrammeMap_MstInstitute]
GO
ALTER TABLE [dbo].[MstInstituteProgrammeMap]  WITH CHECK ADD  CONSTRAINT [FK_MstInstituteProgrammeMap_MstProgramme] FOREIGN KEY([ProgrammeId])
REFERENCES [dbo].[MstProgramme] ([Id])
GO
ALTER TABLE [dbo].[MstInstituteProgrammeMap] CHECK CONSTRAINT [FK_MstInstituteProgrammeMap_MstProgramme]
GO
ALTER TABLE [dbo].[MstPaper]  WITH CHECK ADD  CONSTRAINT [FK_MstPaper_MstSubject] FOREIGN KEY([SubjectId])
REFERENCES [dbo].[MstSubject] ([Id])
GO
ALTER TABLE [dbo].[MstPaper] CHECK CONSTRAINT [FK_MstPaper_MstSubject]
GO
ALTER TABLE [dbo].[MstPaperTeachingLearningMap]  WITH NOCHECK ADD  CONSTRAINT [FK_MstPaperTeachingLearningMap_MstAssessmentMethod] FOREIGN KEY([AssessmentMethodId])
REFERENCES [dbo].[MstAssessmentMethod] ([Id])
GO
ALTER TABLE [dbo].[MstPaperTeachingLearningMap] CHECK CONSTRAINT [FK_MstPaperTeachingLearningMap_MstAssessmentMethod]
GO
ALTER TABLE [dbo].[MstPaperTeachingLearningMap]  WITH CHECK ADD  CONSTRAINT [FK_MstPaperTeachingLearningMap_MstPaper] FOREIGN KEY([PaperId])
REFERENCES [dbo].[MstPaper] ([Id])
GO
ALTER TABLE [dbo].[MstPaperTeachingLearningMap] CHECK CONSTRAINT [FK_MstPaperTeachingLearningMap_MstPaper]
GO
ALTER TABLE [dbo].[MstPaperTeachingLearningMap]  WITH CHECK ADD  CONSTRAINT [FK_MstPaperTeachingLearningMap_MstTeachingLearningMethod] FOREIGN KEY([TeachingLearningMethodId])
REFERENCES [dbo].[MstTeachingLearningMethod] ([Id])
GO
ALTER TABLE [dbo].[MstPaperTeachingLearningMap] CHECK CONSTRAINT [FK_MstPaperTeachingLearningMap_MstTeachingLearningMethod]
GO
ALTER TABLE [dbo].[MstProgramme]  WITH CHECK ADD  CONSTRAINT [FK_MstProgramme_MstEvaluation] FOREIGN KEY([EvaluationId])
REFERENCES [dbo].[MstEvaluation] ([Id])
GO
ALTER TABLE [dbo].[MstProgramme] CHECK CONSTRAINT [FK_MstProgramme_MstEvaluation]
GO
ALTER TABLE [dbo].[MstProgramme]  WITH CHECK ADD  CONSTRAINT [FK_MstProgramme_MstFaculty] FOREIGN KEY([FacultyId])
REFERENCES [dbo].[MstFaculty] ([Id])
GO
ALTER TABLE [dbo].[MstProgramme] CHECK CONSTRAINT [FK_MstProgramme_MstFaculty]
GO
ALTER TABLE [dbo].[MstProgramme]  WITH CHECK ADD  CONSTRAINT [FK_MstProgramme_MstInstructionMedium] FOREIGN KEY([InstructionMediumId])
REFERENCES [dbo].[MstInstructionMedium] ([Id])
GO
ALTER TABLE [dbo].[MstProgramme] CHECK CONSTRAINT [FK_MstProgramme_MstInstructionMedium]
GO
ALTER TABLE [dbo].[MstProgramme]  WITH CHECK ADD  CONSTRAINT [FK_MstProgramme_MstProgrammeLevel] FOREIGN KEY([ProgrammeLevelId])
REFERENCES [dbo].[MstProgrammeLevel] ([Id])
GO
ALTER TABLE [dbo].[MstProgramme] CHECK CONSTRAINT [FK_MstProgramme_MstProgrammeLevel]
GO
ALTER TABLE [dbo].[MstProgramme]  WITH CHECK ADD  CONSTRAINT [FK_MstProgramme_MstProgrammeMode] FOREIGN KEY([ProgrammeModeId])
REFERENCES [dbo].[MstProgrammeMode] ([Id])
GO
ALTER TABLE [dbo].[MstProgramme] CHECK CONSTRAINT [FK_MstProgramme_MstProgrammeMode]
GO
ALTER TABLE [dbo].[MstProgramme]  WITH CHECK ADD  CONSTRAINT [FK_MstProgramme_MstProgrammeType] FOREIGN KEY([ProgrammeTypeId])
REFERENCES [dbo].[MstProgrammeType] ([Id])
GO
ALTER TABLE [dbo].[MstProgramme] CHECK CONSTRAINT [FK_MstProgramme_MstProgrammeType]
GO
ALTER TABLE [dbo].[MstProgrammeBranchMap]  WITH CHECK ADD  CONSTRAINT [FK_MstProgrammeBranchMap_MstProgramme] FOREIGN KEY([ProgrammeId])
REFERENCES [dbo].[MstProgramme] ([Id])
GO
ALTER TABLE [dbo].[MstProgrammeBranchMap] CHECK CONSTRAINT [FK_MstProgrammeBranchMap_MstProgramme]
GO
ALTER TABLE [dbo].[MstProgrammeBranchMap]  WITH CHECK ADD  CONSTRAINT [FK_MstProgrammeBranchMap_MstSpecialisation] FOREIGN KEY([SpecialisationId])
REFERENCES [dbo].[MstSpecialisation] ([Id])
GO
ALTER TABLE [dbo].[MstProgrammeBranchMap] CHECK CONSTRAINT [FK_MstProgrammeBranchMap_MstSpecialisation]
GO
ALTER TABLE [dbo].[MstProgrammeBranchMap]  WITH CHECK ADD  CONSTRAINT [FK_MstProgrammeBranchMap_MstSubSpecialisation] FOREIGN KEY([SubSpecialisationId])
REFERENCES [dbo].[MstSubSpecialisation] ([Id])
GO
ALTER TABLE [dbo].[MstProgrammeBranchMap] CHECK CONSTRAINT [FK_MstProgrammeBranchMap_MstSubSpecialisation]
GO
ALTER TABLE [dbo].[MstProgrammePart]  WITH CHECK ADD  CONSTRAINT [FK_MstProgrammePart_MstExaminationPattern] FOREIGN KEY([ExamPatternId])
REFERENCES [dbo].[MstExaminationPattern] ([Id])
GO
ALTER TABLE [dbo].[MstProgrammePart] CHECK CONSTRAINT [FK_MstProgrammePart_MstExaminationPattern]
GO
ALTER TABLE [dbo].[MstProgrammePart]  WITH CHECK ADD  CONSTRAINT [FK_MstProgrammePart_MstProgramme] FOREIGN KEY([ProgrammeId])
REFERENCES [dbo].[MstProgramme] ([Id])
GO
ALTER TABLE [dbo].[MstProgrammePart] CHECK CONSTRAINT [FK_MstProgrammePart_MstProgramme]
GO
ALTER TABLE [dbo].[MstProgrammePartTermPaperMap]  WITH CHECK ADD  CONSTRAINT [FK__MstProgrammePartTerm] FOREIGN KEY([PartTermId])
REFERENCES [dbo].[MstProgrammePartTerm] ([Id])
GO
ALTER TABLE [dbo].[MstProgrammePartTermPaperMap] CHECK CONSTRAINT [FK__MstProgrammePartTerm]
GO
ALTER TABLE [dbo].[MstProgrammePartTermPaperMap]  WITH CHECK ADD  CONSTRAINT [FK_MstPaper] FOREIGN KEY([PaperId])
REFERENCES [dbo].[MstPaper] ([Id])
GO
ALTER TABLE [dbo].[MstProgrammePartTermPaperMap] CHECK CONSTRAINT [FK_MstPaper]
GO
ALTER TABLE [dbo].[MstSpecialisation]  WITH CHECK ADD  CONSTRAINT [FK_MstSpecialisation_MstFaculty] FOREIGN KEY([FacultyId])
REFERENCES [dbo].[MstFaculty] ([Id])
GO
ALTER TABLE [dbo].[MstSpecialisation] CHECK CONSTRAINT [FK_MstSpecialisation_MstFaculty]
GO
ALTER TABLE [dbo].[MstSpecialisation]  WITH CHECK ADD  CONSTRAINT [FK_MstSpecialisation_MstInstitute] FOREIGN KEY([InstituteId])
REFERENCES [dbo].[MstInstitute] ([Id])
GO
ALTER TABLE [dbo].[MstSpecialisation] CHECK CONSTRAINT [FK_MstSpecialisation_MstInstitute]
GO
ALTER TABLE [dbo].[MstStudent]  WITH CHECK ADD  CONSTRAINT [FK_MstStudent_AdmExtraAct] FOREIGN KEY([ActivityId])
REFERENCES [dbo].[AdmExtraAct] ([Id])
GO
ALTER TABLE [dbo].[MstStudent] CHECK CONSTRAINT [FK_MstStudent_AdmExtraAct]
GO
ALTER TABLE [dbo].[MstStudent]  WITH CHECK ADD  CONSTRAINT [FK_MstStudent_AdmExtraCuriculam] FOREIGN KEY([ParticipationLevelsId])
REFERENCES [dbo].[AdmExtraCuriculam] ([Id])
GO
ALTER TABLE [dbo].[MstStudent] CHECK CONSTRAINT [FK_MstStudent_AdmExtraCuriculam]
GO
ALTER TABLE [dbo].[MstStudent]  WITH CHECK ADD  CONSTRAINT [FK_MstStudent_AdmExtraCuriculamActivity] FOREIGN KEY([SecuredRankId])
REFERENCES [dbo].[AdmExtraCuriculamActivity] ([Id])
GO
ALTER TABLE [dbo].[MstStudent] CHECK CONSTRAINT [FK_MstStudent_AdmExtraCuriculamActivity]
GO
ALTER TABLE [dbo].[MstStudent]  WITH CHECK ADD  CONSTRAINT [FK_MstStudent_BloodGroup] FOREIGN KEY([BloodGroupId])
REFERENCES [dbo].[BloodGroup] ([Id])
GO
ALTER TABLE [dbo].[MstStudent] CHECK CONSTRAINT [FK_MstStudent_BloodGroup]
GO
ALTER TABLE [dbo].[MstStudent]  WITH CHECK ADD  CONSTRAINT [FK_MstStudent_CommunicationLanguage] FOREIGN KEY([CommunicationLanguageId])
REFERENCES [dbo].[CommunicationLanguage] ([Id])
GO
ALTER TABLE [dbo].[MstStudent] CHECK CONSTRAINT [FK_MstStudent_CommunicationLanguage]
GO
ALTER TABLE [dbo].[MstStudent]  WITH CHECK ADD  CONSTRAINT [FK_MstStudent_CountryMaster] FOREIGN KEY([CountryIdOfCitizenship])
REFERENCES [dbo].[CountryMaster] ([Id])
GO
ALTER TABLE [dbo].[MstStudent] CHECK CONSTRAINT [FK_MstStudent_CountryMaster]
GO
ALTER TABLE [dbo].[MstStudent]  WITH CHECK ADD  CONSTRAINT [FK_MstStudent_CountryMaster1] FOREIGN KEY([PermanentCountryId])
REFERENCES [dbo].[CountryMaster] ([Id])
GO
ALTER TABLE [dbo].[MstStudent] CHECK CONSTRAINT [FK_MstStudent_CountryMaster1]
GO
ALTER TABLE [dbo].[MstStudent]  WITH CHECK ADD  CONSTRAINT [FK_MstStudent_CountryMaster2] FOREIGN KEY([CurrentCountryId])
REFERENCES [dbo].[CountryMaster] ([Id])
GO
ALTER TABLE [dbo].[MstStudent] CHECK CONSTRAINT [FK_MstStudent_CountryMaster2]
GO
ALTER TABLE [dbo].[MstStudent]  WITH CHECK ADD  CONSTRAINT [FK_MstStudent_DistrictMaster] FOREIGN KEY([PermanentDistrictId])
REFERENCES [dbo].[DistrictMaster] ([Id])
GO
ALTER TABLE [dbo].[MstStudent] CHECK CONSTRAINT [FK_MstStudent_DistrictMaster]
GO
ALTER TABLE [dbo].[MstStudent]  WITH CHECK ADD  CONSTRAINT [FK_MstStudent_DistrictMaster1] FOREIGN KEY([CurrentDistrictId])
REFERENCES [dbo].[DistrictMaster] ([Id])
GO
ALTER TABLE [dbo].[MstStudent] CHECK CONSTRAINT [FK_MstStudent_DistrictMaster1]
GO
ALTER TABLE [dbo].[MstStudent]  WITH CHECK ADD  CONSTRAINT [FK_MstStudent_GenMaritalStatus] FOREIGN KEY([MaritalStatusId])
REFERENCES [dbo].[GenMaritalStatus] ([Id])
GO
ALTER TABLE [dbo].[MstStudent] CHECK CONSTRAINT [FK_MstStudent_GenMaritalStatus]
GO
ALTER TABLE [dbo].[MstStudent]  WITH CHECK ADD  CONSTRAINT [FK_MstStudent_MaritalStatusId] FOREIGN KEY([MaritalStatusId])
REFERENCES [dbo].[GenMaritalStatus] ([Id])
GO
ALTER TABLE [dbo].[MstStudent] CHECK CONSTRAINT [FK_MstStudent_MaritalStatusId]
GO
ALTER TABLE [dbo].[MstStudent]  WITH CHECK ADD  CONSTRAINT [FK_MstStudent_MotherTongue] FOREIGN KEY([MotherTongueId])
REFERENCES [dbo].[MotherTongue] ([Id])
GO
ALTER TABLE [dbo].[MstStudent] CHECK CONSTRAINT [FK_MstStudent_MotherTongue]
GO
ALTER TABLE [dbo].[MstStudent]  WITH CHECK ADD  CONSTRAINT [FK_MstStudent_Occupation] FOREIGN KEY([OccupationIdOfFather])
REFERENCES [dbo].[GenOccupation] ([Id])
GO
ALTER TABLE [dbo].[MstStudent] CHECK CONSTRAINT [FK_MstStudent_Occupation]
GO
ALTER TABLE [dbo].[MstStudent]  WITH CHECK ADD  CONSTRAINT [FK_MstStudent_Occupation1] FOREIGN KEY([OccupationIdOfMother])
REFERENCES [dbo].[GenOccupation] ([Id])
GO
ALTER TABLE [dbo].[MstStudent] CHECK CONSTRAINT [FK_MstStudent_Occupation1]
GO
ALTER TABLE [dbo].[MstStudent]  WITH CHECK ADD  CONSTRAINT [FK_MstStudent_Occupation2] FOREIGN KEY([OccupationIdOfGuardian])
REFERENCES [dbo].[GenOccupation] ([Id])
GO
ALTER TABLE [dbo].[MstStudent] CHECK CONSTRAINT [FK_MstStudent_Occupation2]
GO
ALTER TABLE [dbo].[MstStudent]  WITH CHECK ADD  CONSTRAINT [FK_MstStudent_ReligionMaster] FOREIGN KEY([ReligionId])
REFERENCES [dbo].[ReligionMaster] ([Id])
GO
ALTER TABLE [dbo].[MstStudent] CHECK CONSTRAINT [FK_MstStudent_ReligionMaster]
GO
ALTER TABLE [dbo].[MstStudent]  WITH CHECK ADD  CONSTRAINT [FK_MstStudent_StateMaster] FOREIGN KEY([PermanentStateId])
REFERENCES [dbo].[StateMaster] ([Id])
GO
ALTER TABLE [dbo].[MstStudent] CHECK CONSTRAINT [FK_MstStudent_StateMaster]
GO
ALTER TABLE [dbo].[MstStudent]  WITH CHECK ADD  CONSTRAINT [FK_MstStudent_StateMaster1] FOREIGN KEY([CurrentStateId])
REFERENCES [dbo].[StateMaster] ([Id])
GO
ALTER TABLE [dbo].[MstStudent] CHECK CONSTRAINT [FK_MstStudent_StateMaster1]
GO
ALTER TABLE [dbo].[MstSubSpecialisation]  WITH CHECK ADD  CONSTRAINT [FK_MstSubSpecialisation_MstSpecialisation] FOREIGN KEY([SpecialisationId])
REFERENCES [dbo].[MstSpecialisation] ([Id])
GO
ALTER TABLE [dbo].[MstSubSpecialisation] CHECK CONSTRAINT [FK_MstSubSpecialisation_MstSpecialisation]
GO
EXEC sys.sp_addextendedproperty @name=N'MS_Description', @value=N'Inactive in case name change or modified' , @level0type=N'SCHEMA',@level0name=N'dbo', @level1type=N'TABLE',@level1name=N'IncInstitutePartTermPaperMap', @level2type=N'COLUMN',@level2name=N'IsActive'
GO
EXEC sys.sp_addextendedproperty @name=N'MS_Description', @value=N'Soft Delete' , @level0type=N'SCHEMA',@level0name=N'dbo', @level1type=N'TABLE',@level1name=N'IncInstitutePartTermPaperMap', @level2type=N'COLUMN',@level2name=N'IsDeleted'
GO
EXEC sys.sp_addextendedproperty @name=N'MS_Description', @value=N'Academic Year' , @level0type=N'SCHEMA',@level0name=N'dbo', @level1type=N'TABLE',@level1name=N'IncProgrammeInstance', @level2type=N'COLUMN',@level2name=N'AcademicYearId'
GO
EXEC sys.sp_addextendedproperty @name=N'MS_Description', @value=N'Intake Capacity' , @level0type=N'SCHEMA',@level0name=N'dbo', @level1type=N'TABLE',@level1name=N'IncProgrammeInstance', @level2type=N'COLUMN',@level2name=N'Intake'
GO
EXEC sys.sp_addextendedproperty @name=N'MS_Description', @value=N'Programme Instance' , @level0type=N'SCHEMA',@level0name=N'dbo', @level1type=N'TABLE',@level1name=N'IncProgrammeInstancePart', @level2type=N'COLUMN',@level2name=N'ProgrammeInstanceId'
GO
EXEC sys.sp_addextendedproperty @name=N'MS_Description', @value=N'Address of the Faculty' , @level0type=N'SCHEMA',@level0name=N'dbo', @level1type=N'TABLE',@level1name=N'MstInstitute', @level2type=N'COLUMN',@level2name=N'InstituteAddress'
GO
EXEC sys.sp_addextendedproperty @name=N'MS_Description', @value=N'Code of the city' , @level0type=N'SCHEMA',@level0name=N'dbo', @level1type=N'TABLE',@level1name=N'MstInstitute', @level2type=N'COLUMN',@level2name=N'CityName'
GO
EXEC sys.sp_addextendedproperty @name=N'MS_Description', @value=N'Pincode' , @level0type=N'SCHEMA',@level0name=N'dbo', @level1type=N'TABLE',@level1name=N'MstInstitute', @level2type=N'COLUMN',@level2name=N'Pincode'
GO
EXEC sys.sp_addextendedproperty @name=N'MS_Description', @value=N'Contact No of Faculty' , @level0type=N'SCHEMA',@level0name=N'dbo', @level1type=N'TABLE',@level1name=N'MstInstitute', @level2type=N'COLUMN',@level2name=N'InstituteContactNo'
GO
EXEC sys.sp_addextendedproperty @name=N'MS_Description', @value=N'Fax no of Faculty' , @level0type=N'SCHEMA',@level0name=N'dbo', @level1type=N'TABLE',@level1name=N'MstInstitute', @level2type=N'COLUMN',@level2name=N'InstituteFaxNo'
GO
EXEC sys.sp_addextendedproperty @name=N'MS_Description', @value=N'Email Id of Head of Faculty' , @level0type=N'SCHEMA',@level0name=N'dbo', @level1type=N'TABLE',@level1name=N'MstInstitute', @level2type=N'COLUMN',@level2name=N'InstituteEmail'
GO
EXEC sys.sp_addextendedproperty @name=N'MS_Description', @value=N'Website Url of the Faculty' , @level0type=N'SCHEMA',@level0name=N'dbo', @level1type=N'TABLE',@level1name=N'MstInstitute', @level2type=N'COLUMN',@level2name=N'InstituteUrl'
GO
EXEC sys.sp_addextendedproperty @name=N'MS_Description', @value=N'Inactive in case name change or modified' , @level0type=N'SCHEMA',@level0name=N'dbo', @level1type=N'TABLE',@level1name=N'MstInstitute', @level2type=N'COLUMN',@level2name=N'IsActive'
GO
EXEC sys.sp_addextendedproperty @name=N'MS_Description', @value=N'Soft Delete' , @level0type=N'SCHEMA',@level0name=N'dbo', @level1type=N'TABLE',@level1name=N'MstInstitute', @level2type=N'COLUMN',@level2name=N'IsDeleted'
GO
EXEC sys.sp_addextendedproperty @name=N'MS_Description', @value=N'Name of Paper' , @level0type=N'SCHEMA',@level0name=N'dbo', @level1type=N'TABLE',@level1name=N'MstPaper', @level2type=N'COLUMN',@level2name=N'PaperName'
GO
EXEC sys.sp_addextendedproperty @name=N'MS_Description', @value=N'Code of paper' , @level0type=N'SCHEMA',@level0name=N'dbo', @level1type=N'TABLE',@level1name=N'MstPaper', @level2type=N'COLUMN',@level2name=N'PaperCode'
GO
EXEC sys.sp_addextendedproperty @name=N'MS_Description', @value=N'Name of the Programme (Bachelor of Commerce)' , @level0type=N'SCHEMA',@level0name=N'dbo', @level1type=N'TABLE',@level1name=N'MstProgramme', @level2type=N'COLUMN',@level2name=N'ProgrammeName'
GO
EXEC sys.sp_addextendedproperty @name=N'MS_Description', @value=N'Short name of the Programme (B.Com.)' , @level0type=N'SCHEMA',@level0name=N'dbo', @level1type=N'TABLE',@level1name=N'MstProgramme', @level2type=N'COLUMN',@level2name=N'ProgrammeCode'
GO
EXEC sys.sp_addextendedproperty @name=N'MS_Description', @value=N'Faculty from which the programme is offered' , @level0type=N'SCHEMA',@level0name=N'dbo', @level1type=N'TABLE',@level1name=N'MstProgramme', @level2type=N'COLUMN',@level2name=N'FacultyId'
GO
EXEC sys.sp_addextendedproperty @name=N'MS_Description', @value=N'Level of Programme like Certificate, Under Graduate, Diploma' , @level0type=N'SCHEMA',@level0name=N'dbo', @level1type=N'TABLE',@level1name=N'MstProgramme', @level2type=N'COLUMN',@level2name=N'ProgrammeLevelId'
GO
EXEC sys.sp_addextendedproperty @name=N'MS_Description', @value=N'Mode of Programme: Regular or Distance ' , @level0type=N'SCHEMA',@level0name=N'dbo', @level1type=N'TABLE',@level1name=N'MstProgramme', @level2type=N'COLUMN',@level2name=N'ProgrammeModeId'
GO
EXEC sys.sp_addextendedproperty @name=N'MS_Description', @value=N'Type: General/Technical/Research' , @level0type=N'SCHEMA',@level0name=N'dbo', @level1type=N'TABLE',@level1name=N'MstProgramme', @level2type=N'COLUMN',@level2name=N'ProgrammeTypeId'
GO
EXEC sys.sp_addextendedproperty @name=N'MS_Description', @value=N'Medium of Instruction' , @level0type=N'SCHEMA',@level0name=N'dbo', @level1type=N'TABLE',@level1name=N'MstProgramme', @level2type=N'COLUMN',@level2name=N'InstructionMediumId'
GO
EXEC sys.sp_addextendedproperty @name=N'MS_Description', @value=N'Evaluation : Marks/Direct Grade/Indirect Grade' , @level0type=N'SCHEMA',@level0name=N'dbo', @level1type=N'TABLE',@level1name=N'MstProgramme', @level2type=N'COLUMN',@level2name=N'EvaluationId'
GO
EXEC sys.sp_addextendedproperty @name=N'MS_Description', @value=N'Total Programme duration in Months' , @level0type=N'SCHEMA',@level0name=N'dbo', @level1type=N'TABLE',@level1name=N'MstProgramme', @level2type=N'COLUMN',@level2name=N'ProgrammeDuration'
GO
EXEC sys.sp_addextendedproperty @name=N'MS_Description', @value=N'Validity of Programme in Months' , @level0type=N'SCHEMA',@level0name=N'dbo', @level1type=N'TABLE',@level1name=N'MstProgramme', @level2type=N'COLUMN',@level2name=N'ProgrammeValidity'
GO
EXEC sys.sp_addextendedproperty @name=N'MS_Description', @value=N'Total Year or Parts of the Programme' , @level0type=N'SCHEMA',@level0name=N'dbo', @level1type=N'TABLE',@level1name=N'MstProgramme', @level2type=N'COLUMN',@level2name=N'TotalParts'
GO
